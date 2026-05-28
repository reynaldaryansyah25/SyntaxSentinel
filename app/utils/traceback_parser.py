import re
from pathlib import PurePosixPath

REPO_FILE_EXTENSIONS = {".py", ".txt", ".toml", ".json", ".yaml", ".yml"}
IGNORED_PATH_PARTS = {
    ".venv",
    "venv",
    "site-packages",
    "__pycache__",
    ".tox",
    ".pytest_cache",
}


def trim_trace(trace: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(trace) <= max_chars:
        return trace

    marker = "... trace trimmed ...\n"
    keep = max_chars - len(marker)
    if keep <= 0:
        return trace[-max_chars:]
    return marker + trace[-keep:]


def extract_candidate_file_paths(trace: str) -> list[str]:
    candidates: list[str] = []

    patterns = [
        r'File "([^"]+)", line \d+',
        r"(?m)^([A-Za-z0-9_./\\-]+\.py):\d+:",
        r"(?m)^([A-Za-z0-9_./\\-]+(?:requirements\.txt|pyproject\.toml|package\.json))\b",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, trace):
            normalized = _normalize_repo_path(match.group(1))
            if normalized and _is_candidate_repo_path(normalized):
                candidates.append(normalized)

    return _dedupe_keep_order(candidates)


def extract_python_error_summary(trace: str) -> dict[str, object | None]:
    syntax_error = _extract_syntax_error(trace)
    if syntax_error:
        return syntax_error

    module_error = _extract_named_error(
        trace,
        error_type="ModuleNotFoundError",
        pattern=r"ModuleNotFoundError:\s*(.+)",
    )
    if module_error:
        return module_error

    import_error = _extract_named_error(
        trace,
        error_type="ImportError",
        pattern=r"ImportError:\s*(.+)",
    )
    if import_error:
        return import_error

    assertion_error = _extract_pytest_assertion_error(trace)
    if assertion_error:
        return assertion_error

    generic = _extract_generic_traceback_error(trace)
    if generic:
        return generic

    paths = extract_candidate_file_paths(trace)
    return {
        "error_type": "UnknownError",
        "file_path": paths[0] if paths else None,
        "line_number": None,
        "message": "Unable to extract Python error summary",
    }


def _extract_syntax_error(trace: str) -> dict[str, object | None] | None:
    file_match = list(re.finditer(r'File "([^"]+)", line (\d+)', trace))
    error_match = re.search(r"SyntaxError:\s*(.+)", trace)

    if not error_match:
        return None

    file_path = None
    line_number = None
    if file_match:
        last_file = file_match[-1]
        file_path = _normalize_repo_path(last_file.group(1))
        line_number = int(last_file.group(2))

    return {
        "error_type": "SyntaxError",
        "file_path": file_path,
        "line_number": line_number,
        "message": error_match.group(1).strip(),
    }


def _extract_named_error(
    trace: str,
    *,
    error_type: str,
    pattern: str,
) -> dict[str, object | None] | None:
    error_match = re.search(pattern, trace)
    if not error_match:
        return None

    paths = extract_candidate_file_paths(trace)
    line_number = _extract_last_traceback_line_number(trace)

    return {
        "error_type": error_type,
        "file_path": paths[0] if paths else None,
        "line_number": line_number,
        "message": error_match.group(1).strip(),
    }


def _extract_pytest_assertion_error(trace: str) -> dict[str, object | None] | None:
    assertion_match = re.search(r"(?m)^E\s+AssertionError(?::\s*(.+))?", trace)
    location_match = re.search(r"(?m)^([A-Za-z0-9_./\\-]+\.py):(\d+):\s+AssertionError", trace)

    if not assertion_match and not location_match:
        return None

    file_path = None
    line_number = None
    if location_match:
        file_path = _normalize_repo_path(location_match.group(1))
        line_number = int(location_match.group(2))

    return {
        "error_type": "AssertionError",
        "file_path": file_path,
        "line_number": line_number,
        "message": assertion_match.group(1).strip() if assertion_match and assertion_match.group(1) else "pytest assertion failed",
    }


def _extract_generic_traceback_error(trace: str) -> dict[str, object | None] | None:
    error_match = re.search(r"(?m)^([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception)):\s*(.+)$", trace)
    if not error_match:
        return None

    paths = extract_candidate_file_paths(trace)
    return {
        "error_type": error_match.group(1),
        "file_path": paths[0] if paths else None,
        "line_number": _extract_last_traceback_line_number(trace),
        "message": error_match.group(2).strip(),
    }


def _extract_last_traceback_line_number(trace: str) -> int | None:
    matches = list(re.finditer(r'File "([^"]+)", line (\d+)', trace))
    if not matches:
        return None
    return int(matches[-1].group(2))


def _normalize_repo_path(path: str) -> str | None:
    value = path.strip().replace("\\", "/")
    if not value:
        return None

    parts = [part for part in value.split("/") if part not in {"", "."}]
    lowered = [part.lower() for part in parts]

    for ignored in IGNORED_PATH_PARTS:
        if ignored in lowered:
            return None

    for marker in ("demo-repo", "syntaxsentinel"):
        if marker in lowered:
            index = lowered.index(marker)
            tail = parts[index + 1 :]
            if tail:
                value = "/".join(tail)
                break
    else:
        if value.startswith("/"):
            value = PurePosixPath(value).name

    return value


def _is_candidate_repo_path(path: str) -> bool:
    if path in {"requirements.txt", "package.json", "pyproject.toml"}:
        return True
    suffix = PurePosixPath(path).suffix
    return suffix in REPO_FILE_EXTENSIONS


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result