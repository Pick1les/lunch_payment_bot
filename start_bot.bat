@echo off
chcp 65001 > nul
title Lunch Payment Bot Server

echo 🚀 Запуск Lunch Payment Bot Server...
echo.

if not exist logs mkdir logs

for /f "tokens=1-3 delims=/" %%a in ("%date%") do (
    set day=%%a
    set month=%%b  
    set year=%%c
)
set logfile=logs\bot_%year%-%month%-%day%.log

echo ======================================= >> %logfile%
echo 🚀 Запуск бота: %date% %time% >> %logfile%
echo ======================================= >> %logfile%

:: Дублируем в консоль
echo =======================================
echo 🚀 Запуск бота: %date% %time%
echo =======================================

:main_loop
echo 🔄 Запуск бота...
echo 🔄 Запуск бота... >> %logfile%

:: Запускаем Python
python main.py

:: Сохраняем код ошибки
set exit_code=%errorlevel%

if %exit_code% equ 0 (
    echo ✅ Бот завершился нормально: %date% %time%
    echo ✅ Бот завершился нормально: %date% %time% >> %logfile%
) else (
    echo ❌ Бот завершился с ошибкой: %exit_code%
    echo ❌ Бот завершился с ошибкой: %exit_code% >> %logfile%
)

echo 🔄 Перезапуск через 15 секунд...
echo 🔄 Перезапуск через 15 секунд... >> %logfile%
timeout /t 15 /nobreak > nul
goto main_loop