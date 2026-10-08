"""Optional packaged-app startup checks; all writable app data is disposable."""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import pytest
except Exception:
    pytest = None


def launch_executable(exe_path, seconds=10, require_qt_ready=False):
    exe = Path(exe_path).resolve()
    print(f"Testing {exe}...")
    if not exe.is_file():
        print(f"FAILED: missing executable {exe}")
        return False

    with tempfile.TemporaryDirectory(prefix="vn_sme_exe_smoke_") as run_dir:
        ready_marker = Path(run_dir) / "qt-ready.txt"
        env = os.environ.copy()
        if require_qt_ready:
            env["VN_SME_QA_READY_FILE"] = str(ready_marker)
            env["VN_SME_QA_AUTOQUIT"] = "1"
        try:
            process = subprocess.Popen(
                [str(exe)],
                cwd=run_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
            )
            deadline = time.monotonic() + (90 if require_qt_ready else seconds)
            ready = False
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    output = process.stdout.read() if process.stdout else ""
                    print(
                        f"FAILED: {exe} exited during startup with code "
                        f"{process.returncode}.\n{output}"
                    )
                    return False
                if require_qt_ready and ready_marker.is_file():
                    title = ready_marker.read_text(encoding="utf-8")
                    if "VN SME Ledger" not in title:
                        print(f"FAILED: unexpected Qt window title: {title!r}")
                        return False
                    ready = True
                    break
                time.sleep(0.25)

            if require_qt_ready and not ready:
                print(f"FAILED: Qt window did not report ready within 90 seconds: {exe}")
                return False
            if require_qt_ready:
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    print("FAILED: Qt app did not close cleanly after QA readiness.")
                    return False
                if process.returncode != 0:
                    print(f"FAILED: Qt app exited with code {process.returncode} after readiness.")
                    return False
            else:
                _stop_process_tree(process)
            print(f"SUCCESS: {exe} reached startup readiness.")
            return True
        except OSError as exc:
            print(f"ERROR launching {exe}: {exc}")
            return False
        finally:
            if "process" in locals() and process.poll() is None:
                _stop_process_tree(process)


def _stop_process_tree(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        taskkill = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "taskkill.exe"
        if taskkill.is_file():
            try:
                subprocess.run(
                    [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                pass
    if process.poll() is None:
        process.kill()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass


if pytest is not None:
    @pytest.mark.parametrize("exe_name", [
        "VN_SME_Ledger_Stable.exe",
        "VN_SME_Ledger_PyQt6.exe",
    ])
    def test_executable_smoke(exe_name):
        if os.environ.get("RUN_EXE_TESTS") != "1":
            pytest.skip("Set RUN_EXE_TESTS=1 to run isolated desktop EXE smoke tests.")
        exe = Path(__file__).resolve().parent / "dist" / exe_name
        if not exe.is_file():
            pytest.skip(f"Executable not built: {exe}")
        assert launch_executable(
            exe,
            require_qt_ready=exe_name == "VN_SME_Ledger_PyQt6.exe",
        )


if __name__ == "__main__":
    workspace = Path(__file__).resolve().parent
    results = [
        launch_executable(workspace / "dist" / "VN_SME_Ledger_Stable.exe"),
        launch_executable(
            workspace / "dist" / "VN_SME_Ledger_PyQt6.exe",
            require_qt_ready=True,
        ),
    ]
    if all(results):
        print("ALL TESTS PASSED.")
        raise SystemExit(0)
    print("SOME TESTS FAILED.")
    raise SystemExit(1)
