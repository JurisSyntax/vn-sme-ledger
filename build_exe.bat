@echo off
cd /d "%~dp0"
echo Building VN SME Ledger Suit...
if "%INSTALL_DEPS%"=="1" (
    echo Installing build dependencies because INSTALL_DEPS=1...
    pip install pyinstaller pillow pandas reportlab openpyxl PyQt6 pyqtgraph
) else (
    echo Skipping online dependency install. Set INSTALL_DEPS=1 to install/update build dependencies.
)

echo Building Stable Tkinter version...
python -m PyInstaller --noconsole --onefile ^
    --name "VN_SME_Ledger_Stable" ^
    --icon "logo.ico" ^
    --add-data "presets;presets" ^
    --add-data "logo.ico;." ^
    main.py

echo Building PyQt6 release (in-app Beta v8)...
set "ORIGINAL_PATH=%PATH%"
set "PATH=%CD%\.venv\Scripts;%CD%\.venv\Lib\site-packages\PyQt6\Qt6\bin;%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem"
.venv\Scripts\python.exe -m PyInstaller VN_SME_Ledger_PyQt6.spec --clean -y
set "PYQT_BUILD_EXIT=%ERRORLEVEL%"
set "PATH=%ORIGINAL_PATH%"
if not "%PYQT_BUILD_EXIT%"=="0" (echo *** PyQt6 build failed *** & goto :error)

echo Done! Check the 'dist' folder.
pause
