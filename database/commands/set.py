import time
from models import CommandResults

def setItem(conn, cache, key: str, value: str, exp_type: str | None = None, exp_time: int | None = None) -> CommandResults:
    expires_at = None
    if exp_type:
        expires_at = round(time.time() + (exp_time / 1000 if exp_type == "PX" else exp_time), 4) if exp_type != "PXAT" else exp_time / 1000

    try:
        cursor = conn.execute(
            "INSERT OR REPLACE INTO kv (key, value, expires_at) VALUES (?, ?, ?)",
            (key, value, expires_at)
        )
        conn.commit()

        if cursor.rowcount <= 0:
            raise Exception("Item not set")

    except Exception as e:
        print(f"Database error: {e}")
        raise ConnectionError("Database connection failed") from e

    if cache is not None:
        cache[key] = (value, expires_at)
        cache.move_to_end(key)
    return CommandResults("OK", expires_at)
