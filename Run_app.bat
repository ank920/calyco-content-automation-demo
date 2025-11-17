@echo off
REM ==========================================================
REM start_dashboard.bat
REM Simple: ensure venv, install requirements, run Streamlit
REM Usage: double-click OR run from cmd. Extra Streamlit args forwarded.
REM Example: start_dashboard.bat --server.port 8502
REM ==========================================================

setlocal

echo -------------------------------------------------------
echo Checking for Python...
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found on PATH. Install Python 3.8+ and add to PATH.
    pause
    exit /b 1
)

REM Create venv if it doesn't exist
if not exist "%~dp0venv\Scripts\activate.bat" (
    echo Creating virtual environment 'venv'...
    python -m venv "%~dp0venv"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment found.
)

REM Activate venv
call "%~dp0venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo WARNING: pip upgrade failed; continuing.
)

REM Install requirements if the file exists
if exist "%~dp0requirements.txt" (
    echo Installing packages from requirements.txt...
    python -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo ERROR: Failed to install some packages from requirements.txt
        echo Check the console output above for details.
        pause
        exit /b 1
    )
) else (
    echo No requirements.txt found — skipping package install.
)

REM Ensure streamlit is available (in case not listed in requirements)
python -c "import importlib,sys
try: importlib.import_module('streamlit')
except Exception:
    sys.exit(1)" >nul 2>&1
if errorlevel 1 (
    echo Streamlit not found in venv — installing streamlit...
    python -m pip install streamlit
    if errorlevel 1 (
        echo ERROR: Failed to install Streamlit.
        pause
        exit /b 1
    )
)

REM Run the Streamlit app (forward any args)
echo Launching Streamlit app: streamlit_app\app.py
streamlit run "%~dp0streamlit_app\app.py" %*
if errorlevel 1 (
    echo Streamlit exited with an error.
    pause
    exit /b 1
)

endlocal
exit /b 0
