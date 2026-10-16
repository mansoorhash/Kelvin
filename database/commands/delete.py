def delItem(conn, cache, key: str):
    
    try:
        cursor = conn.execute(
            "DELETE FROM kv WHERE key = ?",
            (key,)
        )

        conn.commit()

    except Exception as e:
        print(f"Database error: {e}")
        raise ConnectionError("Database connection failed") from e
    if cache is not None:
        cache.pop(key, None)

    return cursor.rowcount
