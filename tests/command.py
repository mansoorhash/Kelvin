import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", 6379))

commands = [
    "SET name john",
    "GET name",
    "DEL name",
    "GET name"
]


def encode_command(command):
    arguments = command.split()
    frame = f"*{len(arguments)}\r\n".encode()
    for argument in arguments:
        data = argument.encode()
        frame += f"${len(data)}\r\n".encode() + data + b"\r\n"
    return frame


with client:
    reader = client.makefile("rb")
    for command in commands:
        client.sendall(encode_command(command))

        response = reader.readline()
        print(f"{command} -> {response.decode().strip()}")
        if response.startswith(b"$") and response != b"$-1\r\n":
            print(reader.readline().decode().strip())
