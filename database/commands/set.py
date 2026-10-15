def setItem(conn, key: str, value: str):
    try:
        conn.execute(
            "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
            (key, value)
        )
    except:
        return "Failed to set item"
    return "OK"