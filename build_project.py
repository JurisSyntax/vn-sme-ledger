import subprocess
import sys
import os

def run_cmd(cmd):
    print(f"Executing: {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"Error: Command failed with return code {res.returncode}")
        sys.exit(res.returncode)

def main():
    venv_python = os.path.join(".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        print(f"Error: {venv_python} not found. Please set up the virtual environment.")
        sys.exit(1)

    print("--- Cleaning build and dist folders ---")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            print(f"Removing {folder} folder...")
            # We don't remove dist files if they might be locked, but let's try
            try:
                import shutil
                shutil.rmtree(folder)
            except Exception as e:
                print(f"Warning: could not delete {folder}: {e}")

    print("--- Building Stable Tkinter version ---")
    run_cmd(f'"{venv_python}" -m PyInstaller --noconsole --onefile --name "VN_SME_Ledger_Stable" --icon "logo.ico" --add-data "presets;presets" --add-data "logo.ico;." main.py')

    print("--- Building PyQt6 release (in-app Beta v6) ---")
    run_cmd(f'"{venv_python}" -m PyInstaller --noconsole --onefile --name "VN_SME_Ledger_PyQt6" --icon "logo.ico" --add-data "presets;presets" --add-data "locales;locales" --add-data "config/countries;config/countries" --add-data "logo.ico;." main_qt.py')

    print("--- Running smoke tests on built executables ---")
    run_cmd(f'"{venv_python}" test_exe.py')
    print("ALL BUILDS AND SMOKE TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
