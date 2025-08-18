# #!/usr/bin/env python3
# import time
# import sys
# from bluepy import btle

# SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
# CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"

# class MyDelegate(btle.DefaultDelegate):
#     def __init__(self):
#         super().__init__()
    
#     def handleNotification(self, cHandle, data):
#         try:
#             msg = data.decode("utf-8").strip()
#             print(f"📨 NOTIFICA RICEVUTA: '{msg}' (handle: {cHandle}, len: {len(data)})")
            
#             # --- MODIFICA CHIAVE QUI ---
#             # Se il server ci dice che ha finito, usciamo.
#             if msg == "END":
#                 print("✅ Trasmissione completata. Chiusura client.")
#                 # sys.exit(0) è il modo pulito per terminare il programma
#                 sys.exit(0) 

#         except Exception as e:
#             print(f"❌ Errore decodifica notifica: {e}")
#             print(f"Raw data: {data}")

# def scan_for_esp32():
#     """Scansiona per l'ESP32 con debug dettagliato"""
#     scanner = btle.Scanner()
    
#     # Prova scansioni multiple
#     for attempt in range(3):
#         print(f"🔍 Tentativo di scansione {attempt + 1}/3...")
        
#         try:
#             devices = scanner.scan(10.0)  # 10 secondi per tentativo
#             print(f"📡 Trovati {len(devices)} dispositivi BLE:")
            
#             target = None
#             for i, dev in enumerate(devices):
#                 print(f"\n--- Dispositivo {i+1} ---")
#                 print(f"Indirizzo: {dev.addr}")
#                 print(f"Tipo indirizzo: {dev.addrType}")
#                 print(f"RSSI: {dev.rssi} dB")
                
#                 # Mostra tutti i dati pubblicitari
#                 scan_data = dev.getScanData()
#                 for (adtype, desc, value) in scan_data:
#                     print(f"  {desc}: {value}")
                    
#                     # Cerca per nome completo
#                     if desc == "Complete Local Name" and value == "ESP32-DataSender":
#                         target = dev
#                         print("🎯 Target trovato per nome!")
                        
#                     # Cerca anche per nome breve
#                     elif desc == "Short Local Name" and value == "ESP32-DataSender":
#                         target = dev
#                         print("🎯 Target trovato per nome breve!")
                    
#                     # Cerca per UUID del servizio (più affidabile)
#                     elif desc == "Complete 128b Services" and SERVICE_UUID.lower() in value.lower():
#                         target = dev
#                         print("🎯 Target trovato per UUID servizio!")
            
#             if target:
#                 return target
#             else:
#                 print(f"❌ ESP32 non trovato nel tentativo {attempt + 1}")
#                 if attempt < 2:
#                     print("⏳ Attesa 3 secondi prima del prossimo tentativo...")
#                     time.sleep(3)
        
#         except btle.BTLEException as e:
#             print(f"❌ Errore durante la scansione {attempt + 1}: {e}")
#             if attempt < 2:
#                 print("⏳ Attesa 3 secondi prima del prossimo tentativo...")
#                 time.sleep(3)
    
#     return None

# def connect_and_listen(target_device):
#     """Connetti al dispositivo e ascolta le notifiche"""
#     try:
#         print(f"🔗 Connessione a {target_device.addr}...")
#         p = btle.Peripheral(target_device.addr, target_device.addrType)
#         p.setDelegate(MyDelegate())
        
#         print("🔍 Ricerca servizio...")
#         services = p.getServices()
#         for service in services:
#             print(f"Servizio: {service.uuid}")
        
#         # Trova il servizio specifico
#         service = p.getServiceByUUID(SERVICE_UUID)
#         print(f"✅ Servizio trovato: {SERVICE_UUID}")
        
#         # Trova la caratteristica
#         characteristics = service.getCharacteristics()
#         ch = None
#         for char in characteristics:
#             print(f"Caratteristica: {char.uuid}")
#             if str(char.uuid).upper() == CHARACTERISTIC_UUID.upper():
#                 ch = char
#                 break
        
#         if not ch:
#             print("❌ Caratteristica non trovata")
#             return
        
#         print(f"✅ Caratteristica trovata: {CHARACTERISTIC_UUID}")
#         print(f"Handle: {ch.getHandle()}")
#         print(f"Proprietà: {ch.propertiesToString()}")
        
#         # Mostra i descriptor disponibili
#         descriptors = ch.getDescriptors()
#         print(f"Descriptor disponibili: {len(descriptors)}")
#         for desc in descriptors:
#             print(f"  - {desc.uuid}: {desc}")
        
#         # Abilita notifiche
#         print("📡 Abilitazione notifiche...")
#         try:
#             # Metodo standard per abilitare notifiche
#             p.writeCharacteristic(ch.getHandle() + 1, b"\x01\x00", withResponse=True)
#             print("✅ Notifiche abilitate con metodo standard")
#         except Exception as e:
#             print(f"⚠️ Metodo standard fallito: {e}")
#             try:
#                 # Metodo alternativo
#                 descriptors = ch.getDescriptors()
#                 for desc in descriptors:
#                     if desc.uuid == 0x2902:  # Client Characteristic Configuration
#                         desc.write(b"\x01\x00", withResponse=True)
#                         print("✅ Notifiche abilitate con descriptor")
#                         break
#             except Exception as e2:
#                 print(f"❌ Impossibile abilitare notifiche: {e2}")
#                 return
        
#         print("✅ Notifiche configurate. Aspettando messaggi...")
        
#         # Loop per ricevere notifiche
#         timeout_count = 0
#         max_timeouts = 6  # Aumentato a 6 timeout (30 secondi totali)
        
#         while True:
#             if p.waitForNotifications(5.0):
#                 timeout_count = 0  # Reset del timeout
#                 continue
#             else:
#                 timeout_count += 1
#                 print(f"⏳ Timeout {timeout_count}/{max_timeouts}...")
                
#                 # Verifica se il dispositivo è ancora connesso
#                 try:
#                     # Prova a leggere la caratteristica per verificare la connessione
#                     current_value = ch.read()
#                     print(f"📋 Valore attuale: {current_value.decode('utf-8', errors='ignore')}")
#                 except:
#                     print("❌ Connessione persa")
#                     break
                    
#                 if timeout_count >= max_timeouts:
#                     print("❌ Troppi timeout, disconnessione...")
#                     break
    
#     except btle.BTLEException as e:
#         print(f"❌ Errore BLE: {e}")
#     except KeyboardInterrupt:
#         print("\n🛑 Interruzione utente")
#     finally:
#         try:
#             p.disconnect()
#             print("🔌 Disconnesso")
#         except:
#             pass

# def main():
#     print("=== Client BLE Python ===")
    
#     # Scansiona per l'ESP32
#     target = scan_for_esp32()
    
#     if not target:
#         print("\n❌ ESP32 non trovato. Verifica che:")
#         print("  1. L'ESP32 sia acceso e il codice sia in esecuzione")
#         print("  2. L'ESP32 sia in modalità advertising")
#         print("  3. Bluetooth sia abilitato su questo computer")
#         print("  4. Non ci siano altri dispositivi connessi all'ESP32")
#         return
    
#     print(f"\n🎯 ESP32 trovato: {target.addr}")
    
#     # Connetti e ascolta
#     connect_and_listen(target)

# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         print("\n🛑 Programma interrotto")
#     except Exception as e:
#         print(f"❌ Errore inaspettato: {e}")
#         import traceback
#         traceback.print_exc()




# above linux program
##############################################################################################################################
################################################################################################################################
##############################################################################################################################
################################################################################################################################
##############################################################################################################################
################################################################################################################################
##############################################################################################################################
################################################################################################################################
# below windows program










import asyncio
from bleak import BleakScanner, BleakClient
import struct

CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"

def notification_handler(sender, data):
    time = data[0] | data[1] << 8 | data[2] << 16 | data[3] << 24
    uuid = data[4] | data[5] << 8 
    rssi = data[6] - 255# if data[6] < 128 else data[6] - 256  # signed convertion
    print(f"time: {time}, uuid: {uuid}, rssi: {rssi}")

async def scan_ble():
    targetDevice = 0
    while True:
        devices = await BleakScanner.discover()
        for device in devices:
            print(f"addr: {device.address}, name: {device.name}")
            # if device.address.upper() == "F0:24:F9:0D:F1:7A":
            try:
                if device.name.lower() == "espcomplete":
                    print("✅ Dispositivo trovato!")
                    targetDevice = device
                    break
            except: pass
        
        if targetDevice != 0: break

        if targetDevice is None:
            await asyncio.sleep(2)
    
    # connect as client to the server BLE
    async with BleakClient(targetDevice.address) as client:
        print("Connected")
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

        try:
            while True: await asyncio.sleep(1)
        except Exception as e:
            print("Errore nella lettura della caratteristica:", e)
        except KeyboardInterrupt:
            print("Interrotto dall'utente")
        finally:
            await client.stop_notify(CHARACTERISTIC_UUID)
            print("🔌 Disconnesso")
        

asyncio.run(scan_ble())
