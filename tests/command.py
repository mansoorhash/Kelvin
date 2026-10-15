import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 6379))

commands = [
    "SET name john",
    "GET name",
    "DEL name",
    "GET name"
]

with client:
    for command in commands:
        client.sendall((command + "\n").encode())

        response = client.recv(1024)
        print(f"{command} -> {response.decode().strip()}")