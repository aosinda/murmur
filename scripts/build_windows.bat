@echo off
REM Build Murmur.exe for Windows.
REM Usage: scripts\build_windows.bat

cd /d "%~dp0\.."

echo ==> Building Murmur.exe...

REM Check venv
if not exist ".venv" (
    echo No .venv found. Run: python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
    exit /b 1
)

REM Install pyinstaller if needed
.venv\Scripts\pip install pyinstaller -q

REM Build
.venv\Scripts\pyinstaller ^
    --name Murmur ^
    --windowed ^
    --onedir ^
    --noconfirm ^
    --clean ^
    --add-data "app;app" ^
    --hidden-import pynput ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import sounddevice ^
    --hidden-import numpy ^
    app\main.py

echo.
echo Done! Murmur.exe built in dist\Murmur\
echo Run: dist\Murmur\Murmur.exe
