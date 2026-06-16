"""The judging engine: run a submission against every test case and decide a verdict.

This is the heart of the online judge. It compiles the code **once**, then runs the
compiled program against each test case (sample + hidden), comparing the program's
output to the expected output.

Verdicts (mirrors Codeforces):
    AC  Accepted              - every test case passed
    WA  Wrong Answer          - output differs on some test case
    TLE Time Limit Exceeded   - a test case ran longer than the problem's limit
    RE  Runtime Error         - the program crashed / exited non-zero
    CE  Compilation Error     - the code did not compile

It stops at the **first** failing test case (just like a real judge) and reports how
many cases passed before that.
"""

from pathlib import Path

from app.services.executor import CompilationError, compile_source, run_executable
from app.services.file_manager import generate_file

# The only language the executor supports today. The router rejects others.
SUPPORTED_LANGUAGE = "cpp"


def _normalize(text: str) -> str:
    """Make output comparison forgiving of trailing whitespace / blank lines.

    Real judges don't fail you for a stray trailing newline. We strip whitespace
    at the end of each line and drop trailing empty lines, then compare.
    """
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def judge_submission(
    language: str,
    code: str,
    test_cases: list,
    time_limit_ms: int,
) -> dict:
    """Compile + run ``code`` against ``test_cases`` and return a verdict report.

    ``test_cases`` is a list of rows/dicts with ``input`` and ``expected_output``.
    Returns:
        {"verdict": str, "passed_count": int, "total_count": int,
         "runtime_ms": int, "detail": str}
    """
    total = len(test_cases)

    # 1) Write the code to disk and compile it ONCE.
    source_path = generate_file(language, code)
    try:
        executable_path = compile_source(Path(source_path))
    except CompilationError as error:
        # Hide the server's internal file path from the user-facing compiler error.
        clean_detail = str(error).replace(source_path, "solution.cpp").strip()
        return {
            "verdict": "CE",
            "passed_count": 0,
            "total_count": total,
            "runtime_ms": 0,
            "detail": clean_detail,
        }

    # 2) Run each test case until one fails.
    timeout_seconds = time_limit_ms / 1000
    passed = 0
    max_runtime_ms = 0

    for index, case in enumerate(test_cases, start=1):
        result = run_executable(executable_path, case["input"], timeout_seconds)
        max_runtime_ms = max(max_runtime_ms, result["runtime_ms"])

        if result["timed_out"]:
            return _report("TLE", passed, total, max_runtime_ms,
                           f"Time limit exceeded on test case {index}.")

        if result["returncode"] != 0:
            return _report("RE", passed, total, max_runtime_ms,
                           f"Runtime error on test case {index}.")

        if _normalize(result["stdout"]) != _normalize(case["expected_output"]):
            return _report("WA", passed, total, max_runtime_ms,
                           f"Wrong answer on test case {index}.")

        passed += 1

    # 3) Every test case passed.
    return _report("AC", passed, total, max_runtime_ms, "All test cases passed.")


def _report(verdict: str, passed: int, total: int, runtime_ms: int, detail: str) -> dict:
    """Small helper to build the verdict dictionary consistently."""
    return {
        "verdict": verdict,
        "passed_count": passed,
        "total_count": total,
        "runtime_ms": runtime_ms,
        "detail": detail,
    }
