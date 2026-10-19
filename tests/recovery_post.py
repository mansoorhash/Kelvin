"""Validate state after Kelvin has restarted and replayed its AOF."""

import socket


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

    print("Checking values restored from appendonly.aof")
    expect(
        send(client, reader, "GET", "recovery:persistent"),
        "plain-value",
        "persistent value recovery",
    )
    expect(
        send(client, reader, "GET", "recovery:complex"),
        "hello world — café",
        "complex value recovery",
    )
    expect(
        send(client, reader, "GET", "recovery:long-lived"),
        "still-alive",
        "unexpired value recovery",
    )

    remaining_ttl = send(client, reader, "TTL", "recovery:long-lived")
    if not isinstance(remaining_ttl, int) or remaining_ttl < 0:
        raise AssertionError(
            "long-lived expiration was not restored: "
            f"received TTL {remaining_ttl!r}"
        )

    print("\nChecking values that must remain absent")
    expect(
        send(client, reader, "GET", "recovery:expired"),
        None,
        "expired value recovery",
    )
    expect(
        send(client, reader, "TTL", "recovery:expired"),
        -2,
        "expired value TTL",
    )
    expect(
        send(client, reader, "GET", "recovery:deleted"),
        None,
        "deleted value recovery",
    )
    expect(
        send(client, reader, "EXISTS", "recovery:deleted"),
        0,
        "deleted value existence",
    )

    print("\nCleanup")
    for key in KEYS:
        send(client, reader, "DEL", key)

print("\nAOF restart recovery passed.")
