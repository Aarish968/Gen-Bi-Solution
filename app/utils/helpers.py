def sanitize_sql(sql: str) -> str:
    """Basic guard against destructive SQL statements."""
    forbidden = ["DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT", "UPDATE"]
    upper = sql.upper()
    for keyword in forbidden:
        if keyword in upper:
            raise ValueError(f"Unsafe SQL detected: {keyword}")
    return sql
