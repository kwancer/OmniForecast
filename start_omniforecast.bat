@echo off
echo ==========================================
echo       Starting OmniForecast Platform
echo ==========================================

echo.
echo [1/2] Launching Backend Server (Port 8002)...
start "OmniForecast Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --port 8002"

echo.
echo [2/2] Launching Frontend Server...
start "OmniForecast Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo       System is starting up...
echo ==========================================
echo Backend: http://localhost:8002
echo Frontend: http://localhost:3000
echo.
echo You can close this window, but keep the other two windows open.
pause
