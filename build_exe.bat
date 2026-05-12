@echo off
echo Building VN SME Ledger Suit (Beta v1) - Official...
pip install pyinstaller pillow pandas reportlab openpyxl
python fix_logo.py
python -m PyInstaller --noconsole --onefile ^
    --name "VN_SME_Ledger" ^
    --icon "logo.ico" ^
    --add-data "presets;presets" ^
    --add-data "logo.ico;." ^
    --add-data "logo_fixed.png;." ^
    main.py
echo Done! Check the 'dist' folder.
pause
