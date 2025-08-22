import asyncio
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError
import time
import requests
import json
import uuid
import os
from load_dotenv import load_dotenv
load_dotenv()

CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
PACKETS_RECEIVED = []
base_url = os.environ["BASE_URL"]

# Variabili globali per la sessione
session = requests.Session()
session.headers.update({"Content-Type": "application/json"})
is_logged = False
token = None

def make_request(method, endpoint, data=None):
    """Funzione per fare richieste HTTP al server"""
    url = f"{base_url}{endpoint}"
    try:
        response = session.request(method, url, data=json.dumps(data) if data else None, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore di rete ({e}), restituisco risposta fittizia.")
        return {"status": 1, "message": "Network error"}

def register(username, password):
    """Registra un nuovo utente"""
    payload = {"username": username, "password": password}
    return make_request("POST", "/api/user/register", data=payload)

def login(username, password):
    """Effettua il login e ottiene il token"""
    global is_logged, token
    
    payload = {"username": username, "password": password}
    response = make_request("POST", "/api/user/login", data=payload)
    
    if response and response.get("status") == 0:
        token = response.get("data", {}).get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
            is_logged = True
            print("✅ Login effettuato con successo!")
            return True
    elif response and response.get("status") == 1:
        print("👤 Utente non esistente, procedo con la registrazione...")
        register(username, password)
        return login(username, password)
    else:
        is_logged = False
        print("❌ Errore durante il login")
        return False

def send_data_to_server():
    """Invia i dati processati al server"""
    global PACKETS_RECEIVED
    
    if not is_logged:
        print("❌ Non sei loggato, impossibile inviare dati")
        return
    
    if not PACKETS_RECEIVED:
        print("📭 Nessun dato da inviare")
        return
    
    print(f"📤 Invio {len(PACKETS_RECEIVED)} connessioni al server...")
    
    for packet in PACKETS_RECEIVED:
        timestamp_ms, my_uuid_hex, detected_uuid_hex, rssi = packet
        
        # Prepara il payload per il server
        payload = {
            "user": my_uuid_hex,  # Il nostro UUID
            "match": detected_uuid_hex,  # L'UUID del dispositivo rilevato
            "timestamp": timestamp_ms,  # Timestamp assoluto
            "rssi": rssi  # Intensità del segnale
        }
        
        try:
            response = make_request("POST", "/api/post_connection", data=payload)
            if response and response.get("status") == 0:
                print(f"✅ Connessione inviata: {detected_uuid_hex[:8]}... (RSSI: {rssi})")
            else:
                print(f"❌ Errore invio connessione: {response}")
        except Exception as e:
            print(f"❌ Errore durante l'invio: {e}")
    
    # Pulisci la lista dopo l'invio
    PACKETS_RECEIVED = []
    print("🧹 Dati inviati e buffer pulito")

def process_timestamps():
    """Converte i timestamp relativi in assoluti e invia i dati"""
    global PACKETS_RECEIVED
    
    if not PACKETS_RECEIVED:
        return
    
    print(f"⏱️ Processando {len(PACKETS_RECEIVED)} pacchetti...")
    
    # Il timestamp corrente in millisecondi
    current_timestamp_ms = int(time.time() * 1000)
    
    # L'ultimo pacchetto (quello di riferimento) ha il timestamp relativo più alto
    reference_relative_time = PACKETS_RECEIVED[-1][0]
    
    # Processa ogni pacchetto per convertire da timestamp relativo ad assoluto
    for packet in PACKETS_RECEIVED:
        relative_time = packet[0]
        
        # Calcola la differenza dal timestamp di riferimento
        time_diff = reference_relative_time - relative_time
        
        # Il timestamp assoluto è il timestamp corrente meno la differenza
        absolute_timestamp = current_timestamp_ms - time_diff
        
        # Aggiorna il timestamp nel pacchetto e converte bytes in hex string
        packet[0] = absolute_timestamp
        packet[1] = packet[1].hex() if isinstance(packet[1], (bytes, bytearray)) else str(packet[1])
        packet[2] = packet[2].hex() if isinstance(packet[2], (bytes, bytearray)) else str(packet[2])
    
    # Rimuovi il pacchetto di fine trasmissione (quello con UUID tutto zero)
    PACKETS_RECEIVED = PACKETS_RECEIVED[:-1]
    
    print("✅ Timestamp processati, invio al server...")
    send_data_to_server()

def make_notification_handler(client: BleakClient):
    def notification_handler(sender, data):
        global PACKETS_RECEIVED
        if len(data) >= 13:  # ESP32 invia struct BLElog di 13 bytes (4+8+1)
            time_val = int.from_bytes(data[0:4], byteorder='little')
            my_uuid_bytes = data[4:12]
            uuid_bytes = data[12:20]  # 8 bytes dell'UUID
            rssi = data[20] if data[20] < 128 else data[20] - 256  # Conversione signed
            PACKETS_RECEIVED.append([time_val, my_uuid_bytes, uuid_bytes, rssi])
            print(f"📦 time: {time_val}, my_uuid: {my_uuid_bytes.hex()}, uuid: {uuid_bytes.hex()}, rssi: {rssi}")

            # Check se è il pacchetto di fine trasmissione
            if uuid_bytes == b"\x00" * 8 and rssi == 0:
                print("📴 Pacchetto di fine trasmissione ricevuto -> processo dati...")
                asyncio.create_task(client.disconnect())
                process_timestamps()

        else:
            print(f"⚠️ Dati ricevuti di lunghezza inaspettata: {len(data)} bytes")
            print(f"Raw data: {data.hex()}")
    return notification_handler

async def scan_and_connect():
    while True:
        print("🔍 Cerco il dispositivo 'esp00'...")
        device = await BleakScanner.find_device_by_name("esp00", timeout=10.0)

        if device is None:
            print("❌ Dispositivo esp00 non trovato, riprovo in 5 secondi...")
            await asyncio.sleep(5)
            continue

        print(f"✅ Dispositivo esp00 trovato! ({device.address})")
        
        try:
            async with BleakClient(device, timeout=20.0) as client:
                if not client.is_connected:
                    print("❌ Non è stato possibile connettersi.")
                    continue

                print("✅ Connesso!")
                
                print("🔔 Attivo le notifiche...")
                await client.start_notify(CHARACTERISTIC_UUID, make_notification_handler(client))
                
                print("🎧 In ascolto delle notifiche. Premi Ctrl+C per uscire.")
                # Rimani connesso finché lo script è in esecuzione
                while client.is_connected:
                    await asyncio.sleep(1)
                
                print("🔌 Disconnesso.")

        except BleakError as e:
            print(f"❌ Errore Bleak: {e}")
        except Exception as e:
            print(f"❌ Errore generico: {e}")

        print("🔄 Riavvio il processo...")
        await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        # Prima registra l'utente
        username = "ble_client"  # Puoi cambiare questo
        password = "password123"  # Puoi cambiare questo
        
        print("👤 Registrazione utente...")
        register_response = register(username, password)
        if register_response:
            print(f"📝 Registrazione completata: {register_response}")
        
        # Poi effettua il login
        print("🔑 Effettuo il login...")
        if not login(username, password):
            print("❌ Impossibile effettuare il login, termino il programma")
            exit(1)
        
        print("✅ Autenticazione completata, avvio Bluetooth...")
        
        # Ora avvia la parte Bluetooth
        asyncio.run(scan_and_connect())
    except KeyboardInterrupt:
        print("\n👋 Programma terminato")