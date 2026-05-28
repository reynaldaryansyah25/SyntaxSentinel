def add(a: int, b: int) -> int:
    return a + b


def normalize_name(value: str) -> str:
    return " ".join(value.strip().title().split())


def is_even(number: int) -> bool:
    return number % 2 == 0