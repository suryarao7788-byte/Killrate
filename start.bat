@echo off
title Killrate - Starting...
echo.
echo  ██╗  ██╗██╗██╗     ██╗     ██████╗  █████╗ ████████╗███████╗
echo  ██║ ██╔╝██║██║     ██║     ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝
echo  █████╔╝ ██║██║     ██║     ██████╔╝███████║   ██║   █████╗
echo  ██╔═██╗ ██║██║     ██║     ██╔══██╗██╔══██║   ██║   ██╔══╝
echo  ██║  ██╗██║███████╗███████╗██║  ██║██║  ██║   ██║   ███████╗
echo  ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
echo.
echo  killrate.info
echo  ─────────────────────────────────────────────
echo.

REM Get the directory this batch file lives in
set ROOT=%~dp0

echo [1/2] Starting backend...
start "Killrate Backend" cmd /k "cd /d %ROOT%backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000"

REM Wait a moment for backend to initialise
timeout /t 5 /nobreak >nul

echo [2/2] Starting frontend...
start "Killrate Frontend" cmd /k "cd /d %ROOT%frontend && npx serve dist --listen 5173 --single"

echo.
echo  Both services started.
echo  Cloudflared runs automatically as a Windows service.
echo.
echo  Site: https://killrate.info
echo  API:  https://api.killrate.info
echo.
echo  Close this window at any time - the services will keep running
echo  in their own windows. Close those windows to stop the app.
echo.
pause
