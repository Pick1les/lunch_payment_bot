@echo off
:: Простой запуск без сложного логирования
echo Запуск бота оплаты обедов...
echo Логи пишутся в консоль

:simple_loop
python smart_final_bot.py
echo Бот перезапустится через 5 секунд...
timeout /t 5
goto simple_loop