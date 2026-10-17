import time

def ttlItem(conn, cache, key: str):
    if cache is not None and key in cache:
        cache.move_to_end(key)
        return (int(cache[key][1] - time.time()) if cache[key][1] is not None else -1, cache[key][1])

    try:
        cursor = conn.execute(
            "SELECT value, expires_at FROM kv WHERE key = ?",
            (key,)
        )

        row = cursor.fetchone()
        if row:
            time_remaining = -1
            if row[1] is not None:
                time_remaining = int(row[1] - time.time())
            if cache is not None:
                cache[key] = (row[0], row[1])
            return (time_remaining, row[1])
        return None
        
    except Exception as e:
        print(f"Database error: {e}")
        raise ConnectionError("Database connection failed") from e
