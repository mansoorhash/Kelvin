def existItem(conn, key: str) -> str:
    try:
        cursor = conn.execute(
            "SELECT * FROM kv WHERE key = ?",
            (key,)
        )

        row = cursor.fetchone()
        if row:
            return 1
        return 0
    except Exception as e:
        print(f"Database error: {e}")
        raise ConnectionError("Database connection failed") from e

