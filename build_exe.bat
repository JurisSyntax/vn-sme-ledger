@echo off
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

echo Building PyQt6 release (in-app Beta v6)...
python -m PyInstaller --noconsole --onefile ^
    --name "VN_SME_Ledger_PyQt6" ^
    --icon "logo.ico" ^
    --add-data "presets;presets" ^
    --add-data "locales;locales" ^
    --add-data "config/countries;config/countries" ^
    --add-data "logo.ico;." ^
    main_qt.py

echo Done! Check the 'dist' folder.
pause
