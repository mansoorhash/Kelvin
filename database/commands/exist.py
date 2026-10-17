def existItem(conn, cache, key: str) -> int:
    if cache is not None and key in cache:
        cache.move_to_end(key)
        return (1, cache[key][1])
    try:
        cursor = conn.execute(
            "SELECT * FROM kv WHERE key = ?",
            (key,)
        )

        row = cursor.fetchone()
        if row:
            if cache is not None:
                cache[key] = (row[1], row[2])
            return (1, row[2])
        return 0
    except Exception as e:
        print(f"Database error: {e}")
        raise ConnectionError("Database connection failed") from e

