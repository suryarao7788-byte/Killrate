@echo off
title Killrate - Auto Restart Service
echo.
echo  Killrate Auto-Restart Service
echo  Restarts backend and frontend every 2 hours
echo  ─────────────────────────────────────────────
echo  Press Ctrl+C to stop
echo.

set ROOT=%~dp0

:loop
echo [%time%] Starting services...

REM Kill any existing instances
taskkill /f /im python.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq Killrate Backend" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq Killrate Frontend" >nul 2>&1

REM Wait a moment for processes to die
timeout /t 3 /nobreak >nul

REM Start backend
start "Killrate Backend" cmd /k "cd /d %ROOT%backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000"

REM Wait for backend to initialise before starting frontend
timeout /t 8 /nobreak >nul

REM Start frontend
start "Killrate Frontend" cmd /k "cd /d %ROOT%frontend && npx serve dist --listen 5173 --single"

echo [%time%] Services started. Next restart in 2 hours.
echo.

REM Wait 2 hours (7200 seconds)
timeout /t 7200 /nobreak

goto loop
