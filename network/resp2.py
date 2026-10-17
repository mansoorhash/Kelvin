class RESPProtocolError(ValueError):
    pass


def _read_line(buffer: bytes, start: int):
    end = buffer.find(b"\r\n", start)
    if end == -1:
        return None
    return buffer[start:end], end + 2


def parse_request(buffer: bytes):
    if not buffer:
        return None

    if buffer[:1] != b"*":
        raise RESPProtocolError("expected an array of bulk strings")

    header = _read_line(buffer, 1)
    if header is None:
        return None

    raw_count, position = header
    try:
        count = int(raw_count)
    except ValueError as error:
        raise RESPProtocolError("invalid array length") from error

    if count <= 0:
        raise RESPProtocolError("command array must not be empty")

    arguments = []
    for _ in range(count):
        if position >= len(buffer):
            return None
        if buffer[position:position + 1] != b"$":
            raise RESPProtocolError("expected a bulk string")

        header = _read_line(buffer, position + 1)
        if header is None:
            return None

        raw_length, position = header
        try:
            length = int(raw_length)
        except ValueError as error:
            raise RESPProtocolError("invalid bulk string length") from error

        if length < 0:
            raise RESPProtocolError("null bulk strings are not valid command arguments")

        end = position + length
        if len(buffer) < end + 2:
            return None
        if buffer[end:end + 2] != b"\r\n":
            raise RESPProtocolError("bulk string is not terminated by CRLF")

        arguments.append(buffer[position:end])
        position = end + 2

    return arguments, buffer[position:]


def simple_string(value: str) -> bytes:
    return b"+" + value.encode("utf-8") + b"\r\n"


def error_response(message: str) -> bytes:
    safe_message = message.replace("\r", " ").replace("\n", " ")
    return b"-ERR " + safe_message.encode("utf-8") + b"\r\n"


def integer(value: int) -> bytes:
    return f":{value}\r\n".encode("ascii")


def bulk_string(value: str | bytes | None) -> bytes:
    if value is None:
        return b"$-1\r\n"
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return f"${len(data)}\r\n".encode("ascii") + data + b"\r\n"
