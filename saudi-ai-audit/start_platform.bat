@echo off
echo ========================================
echo Saudi AI Audit Platform - Local Server
echo ========================================
echo.
echo Starting the platform locally...
echo.
echo Once started, access the platform at:
echo   Main Interface: http://localhost:8000
echo   API Documentation: http://localhost:8000/docs
echo   Alternative Docs: http://localhost:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd /d "C:\Users\Nyajlani\saudi-ai-audit"
python server.py

pause