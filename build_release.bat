@echo off
chcp 65001 > nul
echo 🏗️  Создание нового билда Lunch Bot...
echo.

echo 🧹 Очистка старых сборок...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist LunchBot_Release rmdir /s /q LunchBot_Release

echo 📦 Проверка установки PyInstaller...
pip install pyinstaller

echo 🔄 Сборка исполняемого файла...
pyinstaller --onefile ^
    --add-data ".env;." ^
    --add-data "credentials/service_account_key.json;credentials" ^
    --hidden-import=dotenv ^
    --hidden-import=requests ^
    --hidden-import=cryptography ^
    --hidden-import=googleapiclient ^
    --hidden-import=google.oauth2.service_account ^
    --hidden-import=gspread ^
    --hidden-import=logging ^
    --hidden-import=datetime ^
    --hidden-import=json ^
    --hidden-import=os ^
    --hidden-import=time ^
    --hidden-import=re ^
    --hidden-import=typing ^
    main.py

if %errorlevel% neq 0 (
    echo ❌ Ошибка сборки!
    pause
    exit /b 1
)

echo 📁 Создание папки релиза...
mkdir LunchBot_Release
copy dist\main.exe LunchBot_Release\LunchBot.exe
copy .env LunchBot_Release\
copy start_bot.bat LunchBot_Release\
xcopy credentials LunchBot_Release\credentials /E /I /Y

mkdir LunchBot_Release\data
mkdir LunchBot_Release\backups
mkdir LunchBot_Release\logs

echo 📝 Создание инструкции...
echo Lunch Payment Bot - Версия 1.0 > LunchBot_Release\README.txt
echo. >> LunchBot_Release\README.txt
echo Для запуска: >> LunchBot_Release\README.txt
echo 1. Запустите start_bot.bat >> LunchBot_Release\README.txt
echo 2. Бот запустится автоматически >> LunchBot_Release\README.txt
echo. >> LunchBot_Release\README.txt
echo Файлы: >> LunchBot_Release\README.txt
echo - LunchBot.exe - основная программа >> LunchBot_Release\README.txt
echo - .env - настройки >> LunchBot_Release\README.txt
echo - credentials/ - ключи доступа >> LunchBot_Release\README.txt

echo ✅ Билд успешно создан!
echo 📁 Папка: LunchBot_Release
echo.
echo 📋 Содержимое папки:
dir LunchBot_Release

echo.
echo 🚀 Для запуска перейдите в папку LunchBot_Release и запустите start_bot.bat
pause