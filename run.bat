@echo off
setlocal enabledelayedexpansion
echo === VN SME Ledger - Development Launcher ===
echo.

cd /d "%~dp0"

:: 1. Activate Virtual Environment
if exist .venv\Scripts\activate.bat (
    echo [Env] Activating .venv...
    call .venv\Scripts\activate.bat
) else (
    echo [Env] WARNING: .venv not found. Using system Python.
    echo       Run 'python -m venv .venv' to create it.
)

:: 2. Find Python Executable
set "PYTHON_CMD="
for %%P in (python py python3) do (
    %%P --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=%%P"
        goto :found_python
    )
)
:found_python
if "!PYTHON_CMD!"=="" (
    echo [Error] Python is not installed or not in system PATH. Error 9009 will occur.
    pause
    exit /b 1
)

:: 3. Handle 'test' argument
if "%1"=="test" (
    echo.
    echo [Test] Running Backend Logic Tests...
    !PYTHON_CMD! test_backend.py
    set TEST_ERR=!errorlevel!
    if !TEST_ERR! neq 0 (
        echo [Test] *** Backend tests FAILED ***
    ) else (
        echo [Test] Backend tests PASSED.
    )
    
    echo.
    echo [Test] Running Startup Test...
    !PYTHON_CMD! test_startup.py
    if !errorlevel! neq 0 (
        echo [Test] *** Startup test FAILED ***
        set TEST_ERR=1
    ) else (
        echo [Test] Startup test PASSED.
    )
    
    echo.
    echo [Test] Running Full Pytest Suite...
    !PYTHON_CMD! -m pytest
    if !errorlevel! neq 0 (
        echo [Test] *** Pytest suite FAILED ***
        set TEST_ERR=1
    ) else (
        echo [Test] Pytest suite PASSED.
    )
    
    echo.
    pause
    exit /b !TEST_ERR!
)

:: 4. Run Main App
echo [Run] Starting application with !PYTHON_CMD!...
!PYTHON_CMD! main.py

if !errorlevel! neq 0 (
    echo.
    echo [Error] Application exited with code !errorlevel!.
    pause
)
