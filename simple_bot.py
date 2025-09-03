import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (ЗАМЕНИТЕ НА ВАШ РЕАЛЬНЫЙ ТОКЕН!)
BOT_TOKEN = "8246985665:AAGpHgRVwU3t8vHGwE1bfRxrGGgeJWwyAKA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text("✅ Бот работает! Привет!")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда"""
    user = update.message.from_user
    await update.message.reply_text(
        f"Тест пройден успешно! 🚀\n"
        f"Ваш ID: {user.id}\n"
        f"Имя: {user.first_name}"
    )

def main():
    try:
        logger.info("🚀 Запуск бота...")
        
        # Создаем приложение для современной версии
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("test", test))
        
        logger.info("✅ Бот инициализирован. Запускаю поллинг...")
        
        # Запускаем бота
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == '__main__':
    main()