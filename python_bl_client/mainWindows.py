import asyncio
from bleak import BleakScanner, BleakClient

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
