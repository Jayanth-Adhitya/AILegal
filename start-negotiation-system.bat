@echo off
REM Start script for User-to-User Negotiation System (Windows)

echo ==========================================
echo    User-to-User Negotiation System
echo ==========================================
echo.

REM Check if backend is already running
netstat -ano | findstr ":8000" > nul
if %ERRORLEVEL% EQU 0 (
    echo [WARN] Backend already running on port 8000
) else (
    echo [INFO] Starting Backend...
    cd /d "%~dp0"
    start "Backend Server" cmd /c "python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000"
    echo [OK] Backend started
    timeout /t 3 /nobreak > nul
)

REM Check if frontend is already running
netstat -ano | findstr ":3000" > nul
if %ERRORLEVEL% EQU 0 (
    echo [WARN] Frontend already running on port 3000
) else (
    echo [INFO] Starting Frontend...
    cd /d "%~dp0\frontend"

    REM Check if node_modules exists
    if not exist "node_modules" (
        echo [INFO] Installing dependencies...
        call npm install
    )

    start "Frontend Server" cmd /c "npm run dev"
    echo [OK] Frontend started
)

echo.
echo ==========================================
echo    System Started Successfully!
echo ==========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Testing Instructions:
echo 1. Open http://localhost:3000 in two browsers
echo 2. Register two users from different companies
echo 3. User A: Create negotiation -^> Enter User B email
echo 4. User B: Accept negotiation
echo 5. Both: Chat in real-time!
echo.
echo Press any key to continue...
pause > nul
