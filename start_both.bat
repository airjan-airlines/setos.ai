@echo off
echo Starting both Paper Roadmap servers...
echo.

echo Starting Backend Server (FastAPI)...
start "Backend Server" cmd /k "python start_backend.py"

echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak > nul

echo Starting Frontend Server...
start "Frontend Server" cmd /k "python start_frontend.py"

echo.
echo Both servers are starting...
echo Backend will be available at: http://localhost:8000
echo Frontend will be available at: http://localhost:5500
echo.
echo Press any key to close this window...
pause > nul
