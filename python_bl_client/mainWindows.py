import asyncio
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError
import time

CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"


def notification_handler(sender, data):
    if len(data) >= 13:  # ESP32 invia struct BLElog di 13 bytes (4+8+1)
        time_val = int.from_bytes(data[0:4], byteorder='little')
        uuid_bytes = data[4:12]  # 8 bytes dell'UUID
        rssi = data[12] if data[12] < 128 else data[12] - 256  # Conversione signed
        print(f"time: {time_val}, uuid: {uuid_bytes.hex()}, rssi: {rssi}")
    else:
        print(f"Dati ricevuti di lunghezza inaspettata: {len(data)} bytes")
        print(f"Raw data: {data.hex()}")


async def scan_and_connect():
    while True:
        print("🔍 Cerco il dispositivo 'esp00'...")
        # Usa una funzione che cerca specificamente il dispositivo.
        # Questo è più efficiente e riduce la race condition.
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
                await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
                
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
        asyncio.run(scan_and_connect())
    except KeyboardInterrupt:
        print("\n👋 Programma terminato")
