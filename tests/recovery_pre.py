"""Seed data for a manual AOF restart-recovery test.

Run this while Kelvin is running, then stop the server. To verify AOF recovery
rather than SQLite persistence, move ``kelvin.db`` out of the project before
restarting Kelvin. After restarting, run ``python tests/recovery_post.py``.
"""

import socket
import time


HOST = "127.0.0.1"
PORT = 6379

KEYS = (
    "recovery:persistent",
    "recovery:complex",
    "recovery:long-lived",
    "recovery:expired",
    "recovery:deleted",
)


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
        raise RuntimeError(payload.decode("utf-8"))
    if prefix == b":":
        return int(payload)
    if prefix == b"$":
        length = int(payload)
        if length == -1:
            return None
        value = reader.read(length)
        if reader.read(2) != b"\r\n":
            raise ValueError("Invalid bulk-string terminator")
        return value.decode("utf-8")

    raise ValueError(f"Unsupported RESP prefix: {prefix!r}")


def send(client, reader, *arguments):
    command = " ".join(str(argument) for argument in arguments)
    client.sendall(encode_command(*arguments))
    response = read_response(reader)
    print(f"{command:<66} -> {response!r}")
    return response


def expect(actual, expected, description):
    if actual != expected:
        raise AssertionError(
            f"{description}: expected {expected!r}, received {actual!r}"
        )


with socket.create_connection((HOST, PORT)) as client:
    reader = client.makefile("rb")

    print("Cleaning keys left by an earlier recovery run")
    for key in KEYS:
        send(client, reader, "DEL", key)

    print("\nWriting state that must survive restart")
    expect(
        send(client, reader, "SET", "recovery:persistent", "plain-value"),
        "OK",
        "persistent SET",
    )
    expect(
        send(
            client,
            reader,
            "SET",
            "recovery:complex",
            "hello world — café",
        ),
        "OK",
        "complex-value SET",
    )
    expect(
        send(
            client,
            reader,
            "SET",
            "recovery:long-lived",
            "still-alive",
            "EX",
            3600,
        ),
        "OK",
        "long-lived SET",
    )

    print("\nWriting state that should be absent after restart")
    expect(
        send(
            client,
            reader,
            "SET",
            "recovery:expired",
            "short-lived",
            "PX",
            250,
        ),
        "OK",
        "short-lived SET",
    )
    expect(
        send(client, reader, "SET", "recovery:deleted", "remove-me"),
        "OK",
        "deleted-key SET",
    )
    expect(
        send(client, reader, "DEL", "recovery:deleted"),
        1,
        "deleted-key DEL",
    )

    print("\nWaiting for recovery:expired to pass its deadline...")
    time.sleep(0.35)
    expect(
        send(client, reader, "GET", "recovery:expired"),
        None,
        "expired key before restart",
    )

print("\nPre-restart state written successfully.")
print("1. Stop Kelvin.")
print("2. Move kelvin.db aside so the restart must recover from appendonly.aof.")
print("3. Restart Kelvin.")
print("4. Run: python tests/recovery_post.py")
