def getItem(conn, key: str):
    try:
        cursor = conn.execute(
            "SELECT value FROM kv WHERE key = ?",
            (key,)
        )

        row = cursor.fetchone()
        if row:
            return row[0]
        return "Couldn't find item"
        
    except Exception as e:
        print(f"Database error: {e}")
        return "Failed to fetch"