@echo off
chcp 65001 > nul
echo 📅 Запуск бота: %date% %time% >> bot_log.txt
echo 🚀 Запускаю бота оплаты обедов...
python smart_final_bot.py >> bot_log.txt 2>&1
echo ⏹️ Бот остановлен: %date% %time% >> bot_log.txt
pause