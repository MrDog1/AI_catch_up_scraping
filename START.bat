@echo off
cd /d "%~dp0AI_catch_up_scraping"
echo ========================================
echo  AI Catch-up Scraping - Enhanced Start
echo ========================================
echo Working directory: %CD%
echo Platform: Windows

echo.
echo [1/4] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python first.
    pause
    exit /b 1
)

echo.
echo [2/4] Installing/checking pip...
python -m ensurepip --default-pip >nul 2>&1

echo.
echo [3/4] Installing dependencies (this may take a while)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies failed to install
    echo Continuing with available components...
)

echo.
echo [4/4] Configuration test...
echo Testing configuration:
python -c "import json; c=json.load(open('config.json')); print(' - Sheet ID: ' + ('OK' if c['google_sheets']['sheet_id'] and 'SAMPLE' not in c['google_sheets']['sheet_id'] else 'X')); print(' - Credentials: ' + ('OK' if __import__('os').path.exists(c['google_sheets']['credentials_path']) else 'X')); print(' - Gemini API: ' + ('OK' if c['api_keys'].get('gemini_api_key') and 'SAMPLE' not in c['api_keys']['gemini_api_key'] else 'Not configured (optional)'))" 2>nul || echo Configuration test failed

echo.
echo [5/5] Starting application...

REM Check command line arguments for automatic mode
if "%1"=="auto" (
    echo Running in automatic mode (Full system)...
    goto run_full
)

REM If no arguments, check if config exists for automatic selection
if exist "config.json" (
    python -c "import json; c=json.load(open('config.json')); exit(0 if 'SAMPLE' not in c['google_sheets']['sheet_id'] and __import__('os').path.exists(c['google_sheets']['credentials_path']) else 1)" 2>nul
    if errorlevel 1 (
        echo Configuration incomplete. Starting test mode...
        python standalone_processor.py
    ) else (
        echo Configuration detected. Starting full system...
        goto run_full
    )
) else (
    echo No configuration found. Running setup...
    python auto_google_auth.py
    echo.
    echo Please complete the setup above, then restart START.bat
    pause
    exit /b 1
)
goto end

:run_full
python setup_and_run.py

:end

echo.
echo ========================================
echo Check logs\ directory for detailed logs
echo ========================================
pause