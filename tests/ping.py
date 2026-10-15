import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect(("127.0.0.1", 6379))

    reader = client.makefile("rb")

    client.sendall(b"*1\r\n$4\r\nPING\r\n")

    response1 = reader.readline()
    print(f"PING response: {response1.decode().strip()}")
