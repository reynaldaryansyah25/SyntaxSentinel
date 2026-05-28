def is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""
