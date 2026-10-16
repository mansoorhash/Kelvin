def setItem(conn, cache, key: str, value: str):
    try:
        cursor = conn.execute(
            "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()

        if cursor.rowcount <= 0:
            raise Exception("Item not set")

    except Exception as e:
        print(f"Database error: {e}")
        raise ConnectionError("Database connection failed") from e

    if cache is not None:
        cache[key] = value
        cache.move_to_end(key)
    return "OK"
