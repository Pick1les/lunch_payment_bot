@echo off
chcp 65001 > nul
title Lunch Payment Bot Server

:: Создаем папку для логов если нет
if not exist logs mkdir logs

:: Форматируем дату для имени файла
for /f "tokens=1-3 delims=/" %%a in ("%date%") do (
    set day=%%a
    set month=%%b  
    set year=%%c
)
set logfile=logs\bot_%year%-%month%-%day%.log

echo ======================================= >> %logfile%
echo 🚀 Запуск бота: %date% %time% >> %logfile%
echo ======================================= >> %logfile%

:main_loop
echo 🔄 Запуск бота... >> %logfile%
python smart_final_bot.py >> %logfile% 2>&1

:: Анализ кода завершения
if %errorlevel% equ 0 (
    echo ✅ Бот завершился нормально: %date% %time% >> %logfile%
) else (
    echo ❌ Бот завершился с ошибкой: %errorlevel% >> %logfile%
)

echo 🔄 Перезапуск через 15 секунд... >> %logfile%
timeout /t 15 /nobreak > nul
goto main_loop