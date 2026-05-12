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

:: 2. Handle 'test' argument
if "%1"=="test" (
    echo.
    echo [Test] Running Backend Logic Tests...
    python test_backend.py
    if !errorlevel! neq 0 (
        echo [Test] *** Backend tests FAILED ***
    ) else (
        echo [Test] Backend tests PASSED.
    )
    
    echo.
    echo [Test] Running Startup Test...
    python test_startup.py
    if !errorlevel! neq 0 (
        echo [Test] *** Startup test FAILED ***
    ) else (
        echo [Test] Startup test PASSED.
    )
    
    echo.
    pause
    exit /b !errorlevel!
)

:: 3. Run Main App
echo [Run] Starting application from source...
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [Error] Application exited with code %errorlevel%.
    pause
)
