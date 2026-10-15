def delItem(conn, key: str):
    try:
        cursor = conn.execute(
            "DELETE FROM kv WHERE key = ?",
            (key,)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return "Key not found"

    except Exception as e:
        print(f"Database error during delete {e}")
        return "Failed to delete item"
    return "OK"