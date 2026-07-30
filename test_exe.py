import subprocess
import time
import sys
import os

try:
    import pytest
except Exception:
    pytest = None

def launch_executable(exe_path):
    print(f"Testing {exe_path}...")
    try:
        # Start the executable
        process = subprocess.Popen([exe_path])
        
        # Wait a few seconds to let it initialize
        time.sleep(5)
        
        # Check if the process is still running
        if process.poll() is None:
            print(f"SUCCESS: {exe_path} is running properly and did not crash on boot.")
            # Terminate gracefully
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
            return True
        else:
            print(f"FAILED: {exe_path} crashed with exit code {process.returncode}.")
            return False
    except Exception as e:
        print(f"ERROR launching {exe_path}: {e}")
        return False


if pytest is not None:
    @pytest.mark.parametrize("exe_path", [
        "dist/VN_SME_Ledger_Stable.exe",
        "dist/VN_SME_Ledger_PyQt6.exe",
    ])
    def test_executable_smoke(exe_path):
        if os.environ.get("RUN_EXE_TESTS") != "1":
            pytest.skip("Set RUN_EXE_TESTS=1 to run desktop EXE smoke tests.")
        if not os.path.exists(exe_path):
            pytest.skip(f"Executable not built: {exe_path}")
        assert launch_executable(exe_path)

if __name__ == "__main__":
    results = []
    results.append(launch_executable("dist/VN_SME_Ledger_Stable.exe"))
    results.append(launch_executable("dist/VN_SME_Ledger_PyQt6.exe"))
    
    if all(results):
        print("ALL TESTS PASSED.")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED.")
        sys.exit(1)
