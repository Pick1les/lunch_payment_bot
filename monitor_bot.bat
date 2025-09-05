@echo off
:monitor_loop
echo 🔍 Проверяем состояние бота: %time%

tasklist /fi "imagename eq python.exe" /fo table | findstr /i "python" > nul
if %errorlevel% equ 0 (
    echo ✅ Бот работает
) else (
    echo ❌ Бот не запущен! Запускаю...
    start "" /min smart_final_bot.py
)

:: Ждем 1 минуту перед следующей проверкой
timeout /t 60 /nobreak > nul
goto monitor_loop