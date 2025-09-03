import logging
from telegram.ext import Updater, CommandHandler
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (ВАШ ТОКЕН!)
BOT_TOKEN = "8246985665:AAGpHgRVwU3t8vHGwE1bfRxrGGgeJWwyAKA"

def start(bot, update):
    """Обработчик команды /start"""
    user = update.message.from_user
    update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        f"✅ Бот работает на стабильной версии 12.8!\n"
        f"Используй /help для списка команд."
    )

def help_command(bot, update):
    """Обработчик команды /help"""
    help_text = """
📋 Доступные команды:
/start - Начать работу с ботом
/help - Показать справку
/test - Проверить работу бота
/info - Информация о боте

🚀 Версия: python-telegram-bot 12.8
✅ Статус: Стабильная работа
    """
    update.message.reply_text(help_text)

def test_command(bot, update):
    """Тестовая команда"""
    user = update.message.from_user
    update.message.reply_text(
        f"✅ Тест пройден успешно!\n"
        f"👤 Ваш ID: {user.id}\n"
        f"📝 Имя: {user.first_name}\n"
        f"🔗 Username: @{user.username if user.username else 'не указан'}\n"
        f"🎉 Бот работает стабильно!"
    )

def info_command(bot, update):
    """Информация о боте"""
    update.message.reply_text(
        "🤖 Бот: Оплата обеда 'Простая кухня'\n"
        "📚 Версия библиотеки: 12.8 (стабильная)\n"
        "✅ Статус: Полностью рабочий\n"
        "🚀 Следующий шаг: Подключение Google Sheets"
    )

def error_handler(bot, update, error):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {error}")

def main():
    """Основная функция запуска бота"""
    try:
        logger.info("🚀 Запуск бота на проверенной версии 12.8...")
        
        # Создаем updater
        updater = Updater(BOT_TOKEN)
        dp = updater.dispatcher
        
        # Добавляем обработчики
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("test", test_command))
        dp.add_handler(CommandHandler("info", info_command))
        
        # Обработчик ошибок
        dp.add_error_handler(error_handler)
        
        logger.info("✅ Бот инициализирован. Запускаю поллинг...")
        logger.info("📍 Отправьте боту /test для проверки")
        
        # Запускаем бота
        updater.start_polling()
        logger.info("✅ Бот запущен и слушает сообщения...")
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == '__main__':
    main()