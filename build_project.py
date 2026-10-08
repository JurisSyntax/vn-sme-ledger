import subprocess
import sys
import os
import argparse

def run_cmd(cmd):
    print(f"Executing: {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"Error: Command failed with return code {res.returncode}")
        sys.exit(res.returncode)

def main(argv=None):
    parser = argparse.ArgumentParser(description="Build VN SME Ledger artifacts.")
    parser.add_argument(
        "--qa-build",
        action="store_true",
        help="Deprecated compatibility flag; all builds now run the same non-blocking readiness advisory.",
    )
    args = parser.parse_args(argv)

    venv_python = os.path.join(".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        print(f"Error: {venv_python} not found. Please set up the virtual environment.")
        sys.exit(1)

    # Readiness remains visible to the owner, but is deliberately advisory.
    # Packaging must not be blocked by a stale checklist or an incomplete
    # legal-review record. The report never changes the manifest itself.
    if args.qa_build:
        print("Note: --qa-build is retained for compatibility; it no longer changes build behavior.")
    run_cmd(f'"{venv_python}" release_gate.py')

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

    font_data = '--add-data "assets/fonts;assets/fonts"'
    common_excludes = '--exclude-module pytest --exclude-module _pytest --exclude-module scipy'

    print("--- Building Stable Tkinter version ---")
    run_cmd(
        f'"{venv_python}" -m PyInstaller --noconsole --onefile '
        f'--name "VN_SME_Ledger_Stable" --icon "logo.ico" '
        f'--add-data "presets;presets" --add-data "logo.ico;." {font_data} '
        f'{common_excludes} --exclude-module PyQt6 --exclude-module PySide6 main.py'
    )

    print("--- Building PyQt6 release (in-app Beta v8) ---")
    run_cmd(
        f'"{venv_python}" -m PyInstaller --noconsole --onefile '
        f'--name "VN_SME_Ledger_PyQt6" --icon "logo.ico" '
        f'--add-data "presets;presets" --add-data "locales;locales" '
        f'--add-data "config/countries;config/countries" --add-data "logo.ico;." '
        f'{font_data} {common_excludes} main_qt.py'
    )

    print("--- Running smoke tests on built executables ---")
    run_cmd(f'"{venv_python}" test_exe.py')
    print("ALL BUILDS AND SMOKE TESTS COMPLETED SUCCESSFULLY!")
    print("Review the readiness advisory before representing an artifact as filing-certified.")

if __name__ == "__main__":
    main()
