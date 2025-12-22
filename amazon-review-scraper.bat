@echo off
REM Amazon Review Scraper GUI Launcher (Windows)
REM This script launches the GUI version of the Amazon scraper

echo ========================================
echo Amazon Review Scraper - GUI Version
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import selenium, pandas, webdriver_manager" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        pause
        exit /b 1
    )
)

echo.
echo Starting Amazon Review Scraper GUI...
echo.

REM Launch the GUI application
REM Try pythonw first (no console), fallback to start command
pythonw gui_app.py 2>nul
if errorlevel 1 (
    echo Launching GUI in background...
    start "" python gui_app.py
)

echo.
echo GUI launched. You can close this window.