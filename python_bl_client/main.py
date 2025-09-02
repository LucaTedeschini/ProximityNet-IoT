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

session = requests.Session()
session.headers.update({"Content-Type": "application/json"})
is_logged = False
token = None

def make_request(method, endpoint, data=None):
    url = f"{base_url}{endpoint}"
    try:
        response = session.request(method, url, data=json.dumps(data) if data else None, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error ({e}), returning placeholder.")
        return {"status": 1, "message": "Network error"}

def register(username, password):
    payload = {"username": username, "password": password}
    return make_request("POST", "/api/user/register", data=payload)

def login(username, password):
    global is_logged, token
    
    payload = {"username": username, "password": password}
    response = make_request("POST", "/api/user/login", data=payload)
    
    if response and response.get("status") == 0:
        token = response.get("data", {}).get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
            is_logged = True
            print("Login done succesfully!")
            return True
    elif response and response.get("status") == 1:
        print("User do not exists. Registering...")
        register(username, password)
        return login(username, password)
    else:
        is_logged = False
        print("Error during login")
        return False

def send_data_to_server():
    global PACKETS_RECEIVED
    
    if not is_logged:
        print("You are not logged in!")
        return
    
    if not PACKETS_RECEIVED:
        print("No data to send...")
        return
    
    print(f"Sending {len(PACKETS_RECEIVED)} to the server...")
    
    for packet in PACKETS_RECEIVED:
        timestamp_ms, my_uuid_hex, detected_uuid_hex, rssi = packet
        
        payload = {
            "user": my_uuid_hex, 
            "match": detected_uuid_hex, 
            "timestamp": timestamp_ms,  
            "rssi": rssi  
        }
        
        try:
            response = make_request("POST", "/api/post_connection", data=payload)
            if response and response.get("status") == 0:
                print(f"Sent: {detected_uuid_hex[:8]}... (RSSI: {rssi})")
            else:
                print(f"Error sending data: {response}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Pulisci la lista dopo l'invio
    PACKETS_RECEIVED = []
    print("Data sent!")

def process_timestamps():
    global PACKETS_RECEIVED
    
    if not PACKETS_RECEIVED:
        return
    
    print(f"Processing {len(PACKETS_RECEIVED)} packets...")
    
    current_timestamp_ms = int(time.time() * 1000)
    
    reference_relative_time = PACKETS_RECEIVED[-1][0]
    
    for packet in PACKETS_RECEIVED:
        relative_time = packet[0]
        
        time_diff = reference_relative_time - relative_time
        
        absolute_timestamp = current_timestamp_ms - time_diff
        
        packet[0] = absolute_timestamp
        packet[1] = packet[1].hex() if isinstance(packet[1], (bytes, bytearray)) else str(packet[1])
        packet[2] = packet[2].hex() if isinstance(packet[2], (bytes, bytearray)) else str(packet[2])
    
    PACKETS_RECEIVED = PACKETS_RECEIVED[:-1]
    
    print("Packets processed!...")
    send_data_to_server()

def make_notification_handler(client: BleakClient):
    def notification_handler(sender, data):
        global PACKETS_RECEIVED
        if len(data) >= 13:  
            time_val = int.from_bytes(data[0:4], byteorder='little')
            my_uuid_bytes = data[4:12]
            uuid_bytes = data[12:20] 
            rssi = data[20] if data[20] < 128 else data[20] - 256 
            PACKETS_RECEIVED.append([time_val, my_uuid_bytes, uuid_bytes, rssi])
            print(f"Packer received -> time: {time_val}, my_uuid: {my_uuid_bytes.hex()}, uuid: {uuid_bytes.hex()}, rssi: {rssi}")

            if uuid_bytes == b"\x00" * 8 and rssi == 0:
                print("Special packet received -> processing data...")
                asyncio.create_task(client.disconnect())
                process_timestamps()

        else:
            print(f"Malformed packet received: {len(data)} bytes")
            print(f"Raw data: {data.hex()}")
    return notification_handler

async def scan_and_connect():
    while True:
        print("Scanning for 'esp00'...")
        device = await BleakScanner.find_device_by_name("esp00", timeout=10.0)

        if device is None:
            print("Device esp00 not founr, retrying in 5 seconds...")
            await asyncio.sleep(5)
            continue

        print(f"esp00 found! ({device.address})")
        
        try:
            async with BleakClient(device, timeout=20.0) as client:
                if not client.is_connected:
                    print("Could not connect!.")
                    continue

                print("Connected!")
                
                print("Turning on notifications")
                await client.start_notify(CHARACTERISTIC_UUID, make_notification_handler(client))
                
                print("Listening for packets")
                # Rimani connesso finché lo script è in esecuzione
                while client.is_connected:
                    await asyncio.sleep(1)
                
                print("Disconnected")

        except BleakError as e:
            print(f"❌ Bleak Error: {e}")
        except Exception as e:
            print(f"❌ Generic error: {e}")

        print("Restarting...")
        await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        username = "ble_client" 
        password = "password123"
        
        print("Registering user...")
        register_response = register(username, password)
        if register_response:
            print(f"Register phase completed: {register_response}")
        
        # Poi effettua il login
        print("Logging in...")
        if not login(username, password):
            print("Impossible to log in!")
            exit(1)
        
        print("Auth completed. Turning on bluetooth...")
        
        # Ora avvia la parte Bluetooth
        asyncio.run(scan_and_connect())
    except KeyboardInterrupt:
        print("\nQuitting.")