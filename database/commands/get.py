from database.result import CommandResults

def getItem(conn, cache, key: str) -> CommandResults:
    if cache is not None and key in cache:
        cache.move_to_end(key)
        return CommandResults(cache[key][0], cache[key][1])

    try:
        cursor = conn.execute(
            "SELECT value, expires_at FROM kv WHERE key = ?",
            (key,)
        )

        row = cursor.fetchone()
        if row:
            if cache is not None:
                cache[key] = (row[0], row[1])
            return CommandResults(row[0], row[1])
        return CommandResults()
        
    except Exception as e:
        print(f"Database error: {e}")
        raise ConnectionError("Database connection failed") from e
