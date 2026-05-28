import pytest

from app.services.patcher import (
    PatchValidationError,
    build_gitlab_update_action,
    replace_exact_snippet,
    validate_file_scope,
    validate_patch_size,
)


def test_replace_exact_snippet_applies_minimal_change() -> None:
    original = "def add(a, b):\n    return a - b\n"

    fixed = replace_exact_snippet(original, "return a - b", "return a + b")

    assert fixed == "def add(a, b):\n    return a + b\n"


def test_replace_exact_snippet_rejects_missing_original() -> None:
    with pytest.raises(PatchValidationError, match="not found"):
        replace_exact_snippet("print('ok')\n", "print('missing')", "print('fixed')")


def test_replace_exact_snippet_rejects_ambiguous_original() -> None:
    content = "print('same')\nprint('same')\n"

    with pytest.raises(PatchValidationError, match="ambiguous"):
        replace_exact_snippet(content, "print('same')", "print('fixed')")


def test_replace_exact_snippet_rejects_empty_fixed_snippet() -> None:
    with pytest.raises(PatchValidationError, match="Fixed snippet"):
        replace_exact_snippet("print('ok')\n", "print('ok')", "")


def test_replace_exact_snippet_rejects_binary_content() -> None:
    with pytest.raises(PatchValidationError, match="binary"):
        replace_exact_snippet("abc\x00def", "abc", "xyz")


@pytest.mark.parametrize(
    "file_path",
    [
        "app.py",
        "src/app.py",
        "tests/test_app.py",
        "requirements.txt",
        "package.json",
        "pyproject.toml",
    ],
)
def test_validate_file_scope_allows_mvp_files(file_path: str) -> None:
    assert validate_file_scope(file_path) is True


@pytest.mark.parametrize(
    "file_path",
    [
        "../app.py",
        "/tmp/app.py",
        ".git/config",
        "README.md",
        "src/app.js",
        "venv/lib/app.py",
        "site-packages/pkg/core.py",
        "src\\app.py",
    ],
)
def test_validate_file_scope_rejects_unsafe_files(file_path: str) -> None:
    assert validate_file_scope(file_path) is False


def test_validate_patch_size_allows_small_patch() -> None:
    original = "\n".join([f"line {number}" for number in range(20)])
    fixed = original.replace("line 10", "line ten")

    assert validate_patch_size(original, fixed) is True


def test_validate_patch_size_rejects_empty_fixed_content() -> None:
    with pytest.raises(PatchValidationError, match="empty"):
        validate_patch_size("print('ok')\n", "")


def test_validate_patch_size_rejects_noop_patch() -> None:
    with pytest.raises(PatchValidationError, match="does not change"):
        validate_patch_size("print('ok')\n", "print('ok')\n")


def test_validate_patch_size_rejects_large_rewrite() -> None:
    original = "\n".join([f"line {number}" for number in range(20)])
    fixed = "\n".join([f"changed {number}" for number in range(20)])

    with pytest.raises(PatchValidationError, match="too much"):
        validate_patch_size(original, fixed)


def test_build_gitlab_update_action() -> None:
    action = build_gitlab_update_action("src/app.py", "print('fixed')\n")

    assert action == {
        "action": "update",
        "file_path": "src/app.py",
        "content": "print('fixed')\n",
    }


def test_build_gitlab_update_action_rejects_disallowed_file() -> None:
    with pytest.raises(PatchValidationError, match="outside"):
        build_gitlab_update_action("README.md", "Updated docs\n")
