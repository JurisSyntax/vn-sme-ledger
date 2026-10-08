"""Run the daily frontend, backend, workflow, stress, and packaged crash checks."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
REQUIRED_EXES = (
    ROOT / "dist" / "VN_SME_Ledger_Stable.exe",
    ROOT / "dist" / "VN_SME_Ledger_PyQt6.exe",
)

CHECKS = (
    (
        "Static compile, full functional suite, and unexercised-function audit",
        ("function_coverage_audit.py",),
        {},
        900,
    ),
    (
        "Offline, privacy, and online opt-in security audit",
        (
            "-m",
            "pytest",
            "-q",
            "tests/test_offline_security.py",
            "tests/test_online_integrations.py",
            "tests/test_ai_safety.py",
            "tests/test_official_sources.py",
        ),
        {},
        180,
    ),
    ("Stable Tk startup crash check", ("test_startup.py",), {}, 180),
    (
        "PyQt6 startup crash check",
        ("test_startup_qt.py",),
        {"QT_QPA_PLATFORM": "offscreen"},
        180,
    ),
    ("SQLite/backend transaction smoke", ("test_backend.py",), {}, 180),
    ("Accounting volume stress workload", ("qa_accounting_stress.py",), {}, 300),
    (
        "Stable and PyQt6 packaged EXE crash checks",
        ("-m", "pytest", "-q", "test_exe.py"),
        {"RUN_EXE_TESTS": "1"},
        300,
    ),
)


def main() -> int:
    if not PYTHON.is_file():
        print(f"Missing project virtual environment: {PYTHON}", file=sys.stderr)
        return 2

    missing_exes = [path for path in REQUIRED_EXES if not path.is_file()]
    if missing_exes:
        print("Required packaged apps are missing; EXE crash checks cannot pass:")
        for path in missing_exes:
            print(f"- {path}")

    failures: list[str] = []
    for title, args, overrides, timeout in CHECKS:
        print(f"\n=== {title} ===", flush=True)
        env = os.environ.copy()
        env.update(overrides)
        started = time.monotonic()
        try:
            result = subprocess.run(
                [str(PYTHON), *args],
                cwd=ROOT,
                env=env,
                check=False,
                timeout=timeout,
            )
            elapsed = time.monotonic() - started
            if result.returncode == 0:
                print(f"PASS ({elapsed:.1f}s)", flush=True)
            else:
                failures.append(title)
                print(f"FAIL: exit code {result.returncode} ({elapsed:.1f}s)", flush=True)
        except subprocess.TimeoutExpired:
            failures.append(title)
            print(f"FAIL: timed out after {timeout}s", flush=True)
        except OSError as exc:
            failures.append(title)
            print(f"FAIL: could not start check: {exc}", flush=True)

    if missing_exes:
        failures.append("Packaged EXE preflight")

    print("\n=== Daily QA result ===")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(f"{len(failures)} check(s) failed; do not treat this run as release-ready.")
        return 1

    print(f"All {len(CHECKS)} checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
