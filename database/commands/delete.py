def delItem(conn, key: str):
    try:
        conn.execute(
            "DELETE FROM kv WHERE key = ?",
            (key,)
        )

        conn.commit()

    except Exception as e:
        print(f"Database error during delete {e}")
        return "Failed to delete item"
    return "OK"