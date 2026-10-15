def getItem(conn, key: str):
    try:
        cursor = conn.execute(
            "SELECT value FROM kv WHERE key = ?",
            (key,)
        )

        row = cursor.fetchone()
        if row:
            return row[0]
        return None
        
    except Exception as e:
        print(f"Database error: {e}")
        raise ConnectionError("Database connection failed") from e
