import time
def delItem(conn, cache, key: str):

    state = 0
    now = time.time()
    try:
        cursor = conn.execute(
            "DELETE FROM kv WHERE key = ? RETURNING expires_at",
            (key,)
        )
        row = cursor.fetchone()
        expires_at = row[0] if row else None
        conn.commit()
        state = cursor.rowcount    

    except Exception as e:
        print(f"Database error: {e}")
        raise ConnectionError("Database connection failed") from e
    
    if cache is not None and key in cache:
        if cache[key][1] is not None and now >= cache[key][1]:
            state = 0
        cache.pop(key, None)
    elif expires_at is not None and now >= expires_at:
        state = 0

    return state
