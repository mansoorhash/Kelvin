def delItem(conn, key: str):
    try:
        cursor = conn.execute(
            "DELETE FROM kv WHERE key = ?",
            (key,)
        )

        conn.commit()

        return cursor.rowcount

    except Exception as e:
        print(f"Database error: {e}")
        raise ConnectionError("Database connection failed") from e
