@echo off
:loop
tasklist | findstr "python" > nul
if %errorlevel% neq 0 (
    echo ❌ Бот упал! Перезапуск: %date% %time% >> bot_log.txt
    start restart_bot.bat
)
timeout /t 60 /nobreak > nul
goto loop