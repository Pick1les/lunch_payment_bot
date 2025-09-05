@echo off
echo Установка бота как службы...
echo.

:: Проверяем права администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ОШИБКА: Запустите скрипт от имени администратора!
    echo Правой кнопкой -> "Запуск от имени администратора"
    pause
    exit /b 1
)

:: Получаем полный путь к текущей директории
for %%I in ("%~dp0.") do set "CURRENT_DIR=%%~fI"
set "BATCH_PATH=%CURRENT_DIR%\start_bot.bat"

echo Текущая директория: %CURRENT_DIR%
echo Путь к bat-файлу: %BATCH_PATH%
echo.

:: Проверяем существование файла
if not exist "%BATCH_PATH%" (
    echo ОШИБКА: Файл %BATCH_PATH% не найден!
    pause
    exit /b 1
)

:: Создаем задание в планировщике
echo Создаем задание в планировщике задач...
schtasks /create /tn "LunchPaymentBot" ^
           /tr "\"%BATCH_PATH%\"" ^
           /sc onstart ^
           /ru SYSTEM ^
           /rl HIGHEST ^
           /f

if %errorLevel% equ 0 (
    echo ✅ Задание создано: LunchPaymentBot
    echo 📋 Проверьте: Планировщик заданий -> LunchPaymentBot
    echo.
    echo ⚠️  Важно: Служба запустится при следующей перезагрузке системы
) else (
    echo ❌ Ошибка при создании задания
    echo Попробуйте создать задание вручную через Планировщик задач
)

pause