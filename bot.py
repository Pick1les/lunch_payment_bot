import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime, date
import os
import sys

# Добавляем путь к корневой директории
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import BOT_TOKEN, SPREADSHEET_ID, SHEET_NAME, TIMEZONE, REMINDER_TIMES, LOG_LEVEL
except ImportError:
    print("❌ Создайте файл config.py на основе config.example.py и заполните настройки")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
GET_NAME = 1

class LunchPaymentBot:
    def __init__(self):
        self.user_data = self.load_json('data/user_data.json')
        self.payment_data = self.load_json('data/payment_data.json')
        self.setup_google_sheets()
        
    def setup_google_sheets(self):
        """Настройка подключения к Google Sheets"""
        try:
            creds_file = "credentials/service_account_key.json"
            if not os.path.exists(creds_file):
                logger.error("❌ Файл с credentials не найден")
                return None
                
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
            self.gc = gspread.authorize(creds)
            self.spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)
            self.worksheet = self.spreadsheet.worksheet(SHEET_NAME)
            logger.info("✅ Успешное подключение к Google Sheets")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Google Sheets: {e}")

    def load_json(self, filename):
        """Загрузка JSON файла"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки {filename}: {e}")
        return {}

    def save_json(self, filename, data):
        """Сохранение JSON файла"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения {filename}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я бот для напоминаний об оплате обедов.\n"
        "Используй /help для списка команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📋 Доступные команды:
/start - Начать работу с ботом
/help - Показать справку
/register - Зарегистрировать ФИО
/status - Проверить статус
    """
    await update.message.reply_text(help_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

def main():
    """Основная функция запуска бота"""
    try:
        logger.info("🚀 Запуск бота...")
        
        # Создание приложения
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавление обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("✅ Бот инициализирован. Запускаю поллинг...")
        
        # Запуск бота
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == '__main__':
    # Создаем необходимые директории
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('credentials', exist_ok=True)
    
    main()