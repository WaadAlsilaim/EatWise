@echo off
REM ============================================================
REM EatWise Backend - Windows launcher
REM Usage: double-click this file, or run from cmd/PowerShell
REM ============================================================
setlocal

cd /d "%~dp0"

REM Verify Python exists
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python is not installed or not in PATH.
  echo Please install Python 3.11 from https://python.org
  pause
  exit /b 1
)

REM Create virtual environment if missing
if not exist "venv" (
  echo Creating virtual environment...
  python -m venv venv
  if errorlevel 1 (
    echo [ERROR] Failed to create venv.
    pause
    exit /b 1
  )
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\Lib\site-packages\fastapi" (
  echo Installing dependencies...
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
  )
)

REM Copy .env if missing
if not exist ".env" (
  echo Creating .env from .env.example...
  copy /Y .env.example .env >nul
)

REM Initialize database (idempotent)
if not exist "eatwise.db" (
  echo Initializing database with seed data...
  python -m scripts.init_db
)

echo.
echo ============================================================
echo  EatWise Backend is starting...
echo  API docs:    http://127.0.0.1:8000/docs
echo  Health:      http://127.0.0.1:8000/health
echo  Press Ctrl+C to stop.
echo ============================================================
echo.

REM Run the server (hot-reload)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

endlocal
