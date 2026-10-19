import os
import json
import threading

from network.execute.commands import execute

aof_filename = "appendonly.aof"
aof_lock = threading.Lock()

def create_aof_record(command, resp):
    operation = command[0].decode("utf-8").upper()

    if operation != "SET" and operation != "DEL": return None
    elif resp.response != b"+OK\r\n" and resp.response != b":1\r\n": return None

    arguments = [arg.decode("utf-8") for arg in command[1:]]

    if operation == "SET":
        record = [operation] + arguments[:2]
        if resp.expires_at is not None:
            record.extend(["PXAT",str(round(resp.expires_at * 1000)),])

    elif operation == "DEL":
        record = [operation, arguments[0]]
    return record

def append_to_aof(entries, sync=True):
    records = []
    
    for command, resp in entries:
        record = create_aof_record(command, resp)
        if record is not None: records.append(record)

    if not records: return
    
    with aof_lock:
        with open(aof_filename,"a", encoding="utf-8", newline="\n") as f:
            for record in records:
                json.dump(record, f)
                f.write("\n")
            f.flush()
            if sync:
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

def sync_aof():
    with aof_lock:
        with open(aof_filename, "a", encoding="utf-8") as file:
            file.flush()
            os.fsync(file.fileno())