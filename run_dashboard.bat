@echo off
TITLE Asana Live Manhours Dashboard
color 0A

echo ===================================================
echo    Starting Asana Manhours Dashboard Environment
echo ===================================================
echo.

echo [1/3] Checking and installing required packages...
pip install -r requirements.txt

echo.
echo [2/3] Launching Flask Server...
echo The dashboard will be accessible at: http://127.0.0.1:5000
echo (Keep this window open while using the dashboard)
echo.

echo [3/3] Starting app.py...
python app.py

pause