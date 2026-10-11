# Rewriting receiver script to make sure we have a good mechanism set up for UDP packets from board

import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind(("0.0.0.0", 5000))

print("Listening on UDP port 5000...")

while True:
    data, sender = sock.recvfrom(2048)

    print(f"Received {len(data)} bytes from {sender}")
    print(data)