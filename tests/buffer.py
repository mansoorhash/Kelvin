import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect(("127.0.0.1", 6379))

    reader = client.makefile("rb")

    client.sendall(b"SET name john\r\nGET name\r\n")

    response1 = reader.readline()
    print(f"SET response: {response1.decode().strip()}")

    response2 = reader.readline()
    print(f"GET response: {response2.decode().strip()}")