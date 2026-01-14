@echo off
echo Checking dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo Error installing dependencies. Please make sure Python is installed and added to PATH.
    pause
    exit /b
)
echo.
echo Checking for FFmpeg...
python install_ffmpeg.py
echo.
echo Starting Downloader...
python downloader.py
if %errorlevel% neq 0 (
    echo.
    echo The program crashed or closed unexpectedly.
    pause
)
