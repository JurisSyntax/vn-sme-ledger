import subprocess
import time
import sys

def test_executable(exe_path):
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

if __name__ == "__main__":
    results = []
    results.append(test_executable("dist/VN_SME_Ledger_Stable.exe"))
    results.append(test_executable("dist/VN_SME_Ledger_PyQt6.exe"))
    
    if all(results):
        print("ALL TESTS PASSED.")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED.")
        sys.exit(1)
