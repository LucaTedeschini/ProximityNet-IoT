import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9999))

print("Logging UDP packets...")
file = open("results.csv", "w")
file.write("meters,rssi\n")
while True:
    data, addr = sock.recvfrom(1024)
    decoded_data = data.decode()
    decoded_data.strip()
    meters, rssi = decoded_data.split("/")
    meters = int(meters.strip())
    rssi = int(rssi.strip())
    print(f"Received {meters}m and {rssi}dbm")
    file.write(f"{meters},{rssi}\n")
    file.flush()

