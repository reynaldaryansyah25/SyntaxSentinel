"""Safe patching utilities for small CI-healing edits.

The patcher deliberately supports only narrow update operations. It rejects
large rewrites, binary-looking content, empty fixed files, and files outside the
MVP repair scope.
"""

from pathlib import PurePosixPath

ALLOWED_EXACT_FILENAMES = {"requirements.txt", "package.json", "pyproject.toml"}
ALLOWED_SUFFIXES = {".py"}
BLOCKED_PATH_PARTS = {"", ".", "..", ".git", ".venv", "venv", "site-packages", "__pycache__"}
MAX_CHANGED_RATIO = 0.35
MAX_CHANGED_LINES = 80


class PatchValidationError(ValueError):
    """Raised when a proposed patch violates SyntaxSentinel safety rules."""


def replace_exact_snippet(file_content: str, original_snippet: str, fixed_snippet: str) -> str:
    if _looks_binary(file_content):
        raise PatchValidationError("Refusing to patch binary-looking file content.")
    if original_snippet == "":
        raise PatchValidationError("Original snippet must not be empty.")
    if fixed_snippet == "":
        raise PatchValidationError("Fixed snippet must not be empty.")

    occurrences = file_content.count(original_snippet)
    if occurrences == 0:
        raise PatchValidationError("Original snippet was not found in the file content.")
    if occurrences > 1:
        raise PatchValidationError("Original snippet is ambiguous and appears more than once.")

    fixed_content = file_content.replace(original_snippet, fixed_snippet, 1)
    validate_patch_size(file_content, fixed_content)
    return fixed_content


def validate_file_scope(file_path: str) -> bool:
    normalized = _normalize_file_path(file_path)
    path = PurePosixPath(normalized)
    parts = set(path.parts)

    if parts & BLOCKED_PATH_PARTS:
        return False
    if path.is_absolute():
        return False
    if "\\" in file_path:
        return False
    if normalized in ALLOWED_EXACT_FILENAMES:
        return True
    return path.suffix in ALLOWED_SUFFIXES


def validate_patch_size(original_content: str, fixed_content: str) -> bool:
    if fixed_content == "":
        raise PatchValidationError("Fixed content must not be empty.")
    if _looks_binary(original_content) or _looks_binary(fixed_content):
        raise PatchValidationError("Refusing to patch binary-looking file content.")
    if original_content == fixed_content:
        raise PatchValidationError("Patch does not change the file content.")

    original_lines = original_content.splitlines()
    fixed_lines = fixed_content.splitlines()
    changed_lines = _count_changed_lines(original_lines, fixed_lines)
    baseline_lines = max(len(original_lines), 1)
    changed_ratio = changed_lines / baseline_lines

    if changed_lines > MAX_CHANGED_LINES:
        raise PatchValidationError("Patch changes too many lines for the MVP safety policy.")
    if len(original_lines) > 5 and changed_ratio > MAX_CHANGED_RATIO:
        raise PatchValidationError("Patch rewrites too much of the file.")

    return True


def build_gitlab_update_action(file_path: str, fixed_content: str) -> dict[str, str]:
    if not validate_file_scope(file_path):
        raise PatchValidationError(f"File path is outside the allowed patch scope: {file_path}")
    if fixed_content == "":
        raise PatchValidationError("Fixed content must not be empty.")
    if _looks_binary(fixed_content):
        raise PatchValidationError("Refusing to commit binary-looking file content.")

    return {
        "action": "update",
        "file_path": _normalize_file_path(file_path),
        "content": fixed_content,
    }


def _normalize_file_path(file_path: str) -> str:
    return file_path.strip().replace("\\", "/")


def _looks_binary(content: str) -> bool:
    return "\x00" in content


def _count_changed_lines(original_lines: list[str], fixed_lines: list[str]) -> int:
    common_prefix = 0
    max_prefix = min(len(original_lines), len(fixed_lines))
    while common_prefix < max_prefix and original_lines[common_prefix] == fixed_lines[common_prefix]:
        common_prefix += 1

    original_remaining = original_lines[common_prefix:]
    fixed_remaining = fixed_lines[common_prefix:]

    common_suffix = 0
    max_suffix = min(len(original_remaining), len(fixed_remaining))
    while (
        common_suffix < max_suffix
        and original_remaining[-(common_suffix + 1)] == fixed_remaining[-(common_suffix + 1)]
    ):
        common_suffix += 1

    original_changed = len(original_remaining) - common_suffix
    fixed_changed = len(fixed_remaining) - common_suffix
    return max(original_changed, fixed_changed)
