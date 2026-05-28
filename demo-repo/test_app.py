from app import add, is_even, normalize_name


def test_add() -> None:
    assert add(2, 3) == 5


def test_normalize_name() -> None:
    assert normalize_name("  syntax   sentinel  ") == "Syntax Sentinel"


def test_is_even() -> None:
    assert is_even(4) is True
    assert is_even(5) is False