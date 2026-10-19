import os
import json

from network.execute.commands import execute

aof_filename = "appendonly.aof"

def append_to_aof(command, resp):
    expires_at = resp.expires_at
    operation = command[0].decode("utf-8").upper()
    if operation == "SET" and resp.response != b"+OK\r\n": return
    elif operation == "DEL" and resp.response != b":1\r\n": return
    arguments = [arg.decode("utf-8") for arg in command[1:]]
    append_value = [operation] + arguments[:2]
    if operation == "SET" and expires_at is not None:
        append_value.extend(["PXAT", str(round(expires_at*1000))])

    with open(aof_filename,"a", encoding="utf-8", newline="\n") as f:
        json.dump(append_value, f)
        f.write("\n")
        f.flush()

        os.fsync(f.fileno())

def aof_check(cache_size: int):
    try:
        with open(aof_filename, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start = 1):
                command = json.loads(line)
                result = execute(command, cache_size=cache_size, aof=True)
                if result.response.startswith(b"-ERR"):
                    raise RuntimeError(
                        f"AOF replay failed on line {line_number}"
                    )
    except FileNotFoundError:
        pass
    return None

