@echo off
taskkill /f /im python.exe > nul 2>&1
timeout /t 3 /nobreak > nul
start start_bot.bat