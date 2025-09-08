# config.py
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    # Telegram Bot
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required in .env file")
    
    ADMIN_USER_IDS = [int(id.strip()) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id.strip()]
    
    # Google Sheets
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    SHEET_NAME = os.getenv("SHEET_NAME", "Меню")
    
    # Notification Settings
    NOTIFICATION_SETTINGS = {
        'start_time': os.getenv("START_TIME", "10:20"),
        'end_time': os.getenv("END_TIME", "14:00"),
        'reminder_times': ["11:30", "13:00"],
        'check_interval': int(os.getenv("CHECK_INTERVAL", "300"))
    }
    
    # Payment Details
    PAYMENT_DETAILS = {
        "bank": os.getenv("BANK", "Сбербанк"),
        "phone": os.getenv("PAYMENT_PHONE", ""),
        "name": os.getenv("PAYMENT_NAME", ""),
        "comment": os.getenv("PAYMENT_COMMENT", "Оплата обеда")
    }
    
    # Files
    USER_DATA_FILE = "user_data.enc"
    PAYMENTS_FILE = "payments.enc"
    LOG_FILE = "bot.log"
    
    # API
    API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    # Paths
    CREDENTIALS_DIR = "credentials"
    SERVICE_ACCOUNT_KEY = os.path.join(CREDENTIALS_DIR, "service_account_key.json")
    
    # Security
    ENCRYPTION_ENABLED = True

    # Admin settings
    ADMIN_USER_IDS = [int(id.strip()) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id.strip()]
    ADMIN_NOTIFICATION_TIME = os.getenv("ADMIN_NOTIFICATION_TIME", "09:00")
    BACKUP_TIME = os.getenv("BACKUP_TIME", "00:00")
    
    # Admin commands
    ADMIN_COMMANDS = [
        "/stats - Статистика бота",
        "/users - Список пользователей", 
        "/broadcast - Рассылка сообщения",
        "/backup - Создать backup данных",
        "/notify_admin - Уведомление админам",
        "/check_orders - Принудительная проверка заказов"
    ]

# Создаем глобальный экземпляр конфига
config = Config()