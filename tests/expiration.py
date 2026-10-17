import socket
import time


HOST = "127.0.0.1"
PORT = 6379


def encode_command(*arguments):
    frame = f"*{len(arguments)}\r\n".encode("ascii")

    for argument in arguments:
        data = str(argument).encode("utf-8")
        frame += f"${len(data)}\r\n".encode("ascii")
        frame += data + b"\r\n"

    return frame


def read_response(reader):
    first_line = reader.readline()

    if not first_line:
        raise ConnectionError("Server closed the connection")

    prefix = first_line[:1]
    payload = first_line[1:-2]

    if prefix == b"+":
        return payload.decode("utf-8")

    if prefix == b"-":
        return payload.decode("utf-8")

    if prefix == b":":
        return int(payload)

    if prefix == b"$":
        length = int(payload)
        if length == -1:
            return None

        value = reader.read(length)
        terminator = reader.read(2)
        if terminator != b"\r\n":
            raise ValueError("Invalid bulk-string terminator")
        return value.decode("utf-8")

    raise ValueError(f"Unsupported RESP prefix: {prefix!r}")


def send(client, reader, *arguments):
    command = " ".join(str(argument) for argument in arguments)
    client.sendall(encode_command(*arguments))
    response = read_response(reader)
    print(f"{command:<42} -> {response!r}")
    return response


with socket.create_connection((HOST, PORT)) as client:
    reader = client.makefile("rb")

    print("Persistent key")
    send(client, reader, "SET", "debug:persistent", "value")
    send(client, reader, "TTL", "debug:persistent")

    print("\nSecond-based expiration")
    send(client, reader, "SET", "debug:seconds", "value", "EX", 2)
    send(client, reader, "TTL", "debug:seconds")
    send(client, reader, "GET", "debug:seconds")

    print("\nMillisecond expiration and lazy deletion")
    send(client, reader, "SET", "debug:short", "value", "PX", 200)
    send(client, reader, "GET", "debug:short")
    print("Waiting 300 ms...")
    time.sleep(0.3)
    send(client, reader, "GET", "debug:short")
    send(client, reader, "EXISTS", "debug:short")
    send(client, reader, "TTL", "debug:short")

    print("\nDeleting an expired key")
    send(client, reader, "SET", "debug:delete", "value", "PX", 200)
    print("Waiting 300 ms...")
    time.sleep(0.3)
    delete_response = send(client, reader, "DEL", "debug:delete")
    print(f"Expected DEL response: 0; received: {delete_response!r}")

    print("\nReplacing an expiring key clears its TTL")
    send(client, reader, "SET", "debug:replace", "old", "EX", 2)
    send(client, reader, "TTL", "debug:replace")
    send(client, reader, "SET", "debug:replace", "new")
    send(client, reader, "TTL", "debug:replace")

    print("\nCleanup")
    send(client, reader, "DEL", "debug:persistent")
    send(client, reader, "DEL", "debug:seconds")
    send(client, reader, "DEL", "debug:short")
    send(client, reader, "DEL", "debug:delete")
    send(client, reader, "DEL", "debug:replace")
