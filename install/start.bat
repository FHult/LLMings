@echo off
REM LLMings Startup Script for Windows
REM This script starts the LLMings application in production mode

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo Starting LLMings...

REM Check if Python virtual environment exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Checking dependencies...
pip install -r requirements.txt --quiet

REM Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env from .env.example...
        copy .env.example .env
        echo Please edit .env to add your API keys
    )
)

REM Start Ollama if available
where ollama >nul 2>nul
if %errorlevel%==0 (
    echo Starting Ollama...
    start /B ollama serve 2>nul
    timeout /t 2 /nobreak >nul
) else (
    echo Ollama not found. Local models will not be available.
    echo Install from: https://ollama.ai
)

REM Start the backend server
echo Starting backend server on port 8000...
start /B uvicorn app.main:app --host 0.0.0.0 --port 8000

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start serving frontend
echo Starting frontend server on port 3000...
cd static
start /B python -m http.server 3000
cd ..

echo.
echo ========================================
echo LLMings is running!
echo ========================================
echo.
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop all services
echo.

REM Keep the window open
pause
