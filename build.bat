@echo off
echo === VN SME Ledger — Syntax Check + Build ===
echo.

cd /d "C:\Users\AMD\.gemini\antigravity\scratch\vn-sme-ledger"
call .venv\Scripts\activate.bat

echo [Step 1] Checking syntax for all Python files...
echo.

python -m py_compile main.py
if %ERRORLEVEL% NEQ 0 (echo *** SYNTAX ERROR in main.py *** & goto :error)
echo   main.py .............. OK

python -m py_compile db.py
if %ERRORLEVEL% NEQ 0 (echo *** SYNTAX ERROR in db.py *** & goto :error)
echo   db.py ................ OK

python -m py_compile tabs_extra.py
if %ERRORLEVEL% NEQ 0 (echo *** SYNTAX ERROR in tabs_extra.py *** & goto :error)
echo   tabs_extra.py ........ OK

python -m py_compile analytics.py
if %ERRORLEVEL% NEQ 0 (echo *** SYNTAX ERROR in analytics.py *** & goto :error)
echo   analytics.py ......... OK

python -m py_compile config.py
if %ERRORLEVEL% NEQ 0 (echo *** SYNTAX ERROR in config.py *** & goto :error)
echo   config.py ............ OK

python -m py_compile tax_calculator.py
if %ERRORLEVEL% NEQ 0 (echo *** SYNTAX ERROR in tax_calculator.py *** & goto :error)
echo   tax_calculator.py .... OK

python -m py_compile manual.py
if %ERRORLEVEL% NEQ 0 (echo *** SYNTAX ERROR in manual.py *** & goto :error)
echo   manual.py ............ OK

python -m py_compile invoice_gen.py
if %ERRORLEVEL% NEQ 0 (echo *** SYNTAX ERROR in invoice_gen.py *** & goto :error)
echo   invoice_gen.py ....... OK

python -m py_compile market_data.py
if %ERRORLEVEL% NEQ 0 (echo *** SYNTAX ERROR in market_data.py *** & goto :error)
echo   market_data.py ....... OK

echo.
echo All files OK! Starting build...
echo.

echo [Step 2] Building EXE...
pyinstaller VN_SME_Ledger.spec --clean -y
if %ERRORLEVEL% NEQ 0 (echo *** BUILD FAILED *** & goto :error)

echo.
echo ============================================
echo   BUILD SUCCESSFUL!
echo   Output: dist\VN_SME_Ledger\VN_SME_Ledger.exe
echo ============================================
pause
exit /b 0

:error
echo.
echo Build stopped due to error above.
pause
exit /b 1
