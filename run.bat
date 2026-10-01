@echo off
REM One-click start for Windows. Creates a virtual environment on first run.
cd /d "%~dp0backend"

if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
  if errorlevel 1 (
    echo Python was not found. Install Python 3.10+ from python.org and tick "Add to PATH".
    pause
    exit /b 1
  )
)

call venv\Scripts\activate.bat
echo Installing requirements (first run takes a minute)...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
  echo Install failed. See the message above.
  pause
  exit /b 1
)

start "" http://localhost:5000
python app.py
pause
