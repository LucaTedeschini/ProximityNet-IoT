import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 9999))

print("Logging UDP packets...")
while True:
    data, addr = sock.recvfrom(1024)
    print(f"{addr}: {data.decode()}")

