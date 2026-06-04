@echo off
echo Building VN SME Ledger Suit...
pip install pyinstaller pillow pandas reportlab openpyxl PyQt6 pyqtgraph

echo Building Stable Tkinter version...
python -m PyInstaller --noconsole --onefile ^
    --name "VN_SME_Ledger_Stable" ^
    --icon "logo.ico" ^
    --add-data "presets;presets" ^
    --add-data "logo.ico;." ^
    main.py

echo Building New PyQt6 version...
python -m PyInstaller --noconsole --onefile ^
    --name "VN_SME_Ledger_PyQt6" ^
    --icon "logo.ico" ^
    --add-data "presets;presets" ^
    --add-data "logo.ico;." ^
    main_qt.py

echo Done! Check the 'dist' folder.
pause
