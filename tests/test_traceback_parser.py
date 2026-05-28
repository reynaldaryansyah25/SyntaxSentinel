from pathlib import Path

from app.utils.traceback_parser import (
    extract_candidate_file_paths,
    extract_python_error_summary,
    trim_trace,
)


def test_trim_trace_keeps_short_trace() -> None:
    trace = "short trace"

    assert trim_trace(trace, 100) == trace


def test_trim_trace_trims_long_trace_from_end() -> None:
    trace = "a" * 100 + "SyntaxError: expected ':'"

    trimmed = trim_trace(trace, 40)

    assert len(trimmed) <= 40
    assert "expected ':'" in trimmed


def test_extract_candidate_file_paths_ignores_site_packages() -> None:
    trace = '''
  File "/builds/user/project/app.py", line 3, in <module>
  File "/usr/local/lib/python3.11/site-packages/pkg/core.py", line 1, in run
tests/test_app.py:10: AssertionError
'''

    paths = extract_candidate_file_paths(trace)

    assert "app.py" in paths
    assert "tests/test_app.py" in paths
    assert all("site-packages" not in path for path in paths)


def test_extract_syntax_error_summary_from_fixture() -> None:
    trace = Path("tests/fixtures/failed_job_trace_python.txt").read_text()

    summary = extract_python_error_summary(trace)

    assert summary == {
        "error_type": "SyntaxError",
        "file_path": "app.py",
        "line_number": 2,
        "message": "expected ':'",
    }


def test_extract_module_not_found_error_summary() -> None:
    trace = '''
Traceback (most recent call last):
  File "/builds/user/project/test_app.py", line 1, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
'''

    summary = extract_python_error_summary(trace)

    assert summary["error_type"] == "ModuleNotFoundError"
    assert summary["file_path"] == "test_app.py"
    assert summary["line_number"] == 1
    assert summary["message"] == "No module named 'requests'"


def test_extract_import_error_summary() -> None:
    trace = '''
Traceback (most recent call last):
  File "/builds/user/project/app.py", line 1, in <module>
    from math import nope
ImportError: cannot import name 'nope' from 'math'
'''

    summary = extract_python_error_summary(trace)

    assert summary["error_type"] == "ImportError"
    assert summary["file_path"] == "app.py"
    assert summary["line_number"] == 1


def test_extract_pytest_assertion_error_summary() -> None:
    trace = '''
test_app.py:5: AssertionError
E   AssertionError: assert 6 == 5
'''

    summary = extract_python_error_summary(trace)

    assert summary["error_type"] == "AssertionError"
    assert summary["file_path"] == "test_app.py"
    assert summary["line_number"] == 5
    assert summary["message"] == "assert 6 == 5"


def test_extract_generic_error_summary() -> None:
    trace = '''
Traceback (most recent call last):
  File "/builds/user/project/app.py", line 7, in <module>
    run()
ValueError: invalid value
'''

    summary = extract_python_error_summary(trace)

    assert summary["error_type"] == "ValueError"
    assert summary["file_path"] == "app.py"
    assert summary["line_number"] == 7
    assert summary["message"] == "invalid value"