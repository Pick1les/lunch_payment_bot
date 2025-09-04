@echo off
echo 🤖 Проверка состояния бота...
tasklist | findstr "python" > nul
if %errorlevel%==0 (
    echo ✅ Бот работает
) else (
    echo ❌ Бот не запущен
    echo Запускаю перезапуск...
    start restart_bot.bat
)
timeout /t 30