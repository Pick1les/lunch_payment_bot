import requests
import time
import json
import logging
import os
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Ваш токен
BOT_TOKEN = "8246985665:AAGpHgRVwU3t8vHGwE1bfRxrGGgeJWwyAKA"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Файлы для данных
USER_DATA_FILE = "data/user_data.json"
REMINDERS_FILE = "data/reminders.json"

def load_data(filename):
    """Загружает данные из JSON файла"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки {filename}: {e}")
    return {}

def save_data(filename, data):
    """Сохраняет данные в JSON файл"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка сохранения {filename}: {e}")

def send_message(chat_id, text):
    """Отправляет сообщение"""
    url = f"{API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        return None

def get_updates(offset=None):
    """Получает новые сообщения"""
    url = f"{API_URL}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    try:
        response = requests.get(url, params=params, timeout=110)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка получения updates: {e}")
        return {"ok": False, "result": []}

def check_reminders():
    """Проверяет и отправляет напоминания"""
    try:
        reminders = load_data(REMINDERS_FILE)
        user_data = load_data(USER_DATA_FILE)
        current_time = datetime.now()
        
        reminders_to_remove = []
        
        for reminder_id, reminder in reminders.items():
            reminder_time = datetime.fromisoformat(reminder["time"])
            
            if current_time >= reminder_time:
                # Время напоминания настало
                user_id = reminder["user_id"]
                if user_id in user_data and user_data[user_id].get("registered"):
                    send_message(
                        user_id, 
                        f"⏰ Напоминание: {reminder['message']}\n"
                        f"💳 Не забудьте оплатить обед!"
                    )
                    logger.info(f"📨 Отправлено напоминание пользователю {user_id}")
                
                reminders_to_remove.append(reminder_id)
        
        # Удаляем отправленные напоминания
        for reminder_id in reminders_to_remove:
            del reminders[reminder_id]
            save_data(REMINDERS_FILE, reminders)
            
    except Exception as e:
        logger.error(f"Ошибка проверки напоминаний: {e}")

def handle_message(message):
    """Обрабатывает сообщение"""
    chat_id = str(message["chat"]["id"])
    text = message.get("text", "").lower()
    user = message["from"]
    
    # Загружаем данные
    user_data = load_data(USER_DATA_FILE)
    reminders = load_data(REMINDERS_FILE)
    
    # Сохраняем информацию о пользователе
    user_id = str(user["id"])
    if user_id not in user_data:
        user_data[user_id] = {
            "first_name": user.get("first_name", ""),
            "username": user.get("username", ""),
            "last_interaction": datetime.now().isoformat(),
            "registered": False
        }
        logger.info(f"📝 Новый пользователь: {user.get('first_name', 'Unknown')}")
    
    user_data[user_id]["last_interaction"] = datetime.now().isoformat()
    save_data(USER_DATA_FILE, user_data)
    
    if text == "/start":
        send_message(chat_id, "👋 Привет! Я бот для напоминаний об оплате обедов! ✅")
        send_message(chat_id, "Используй /register чтобы зарегистрироваться для уведомлений")
        
    elif text == "/test":
        send_message(chat_id, f"✅ Тест пройден!\nID: {user['id']}\nИмя: {user['first_name']}")
        
    elif text == "/help":
        help_text = """
📋 Команды:
/start - начать работу
/register - регистрация для уведомлений
/test - тест работы бота
/stats - статистика
/remindme - установить напоминание
        """
        send_message(chat_id, help_text)
    
    elif text == "/register":
        user_data[user_id]["registered"] = True
        save_data(USER_DATA_FILE, user_data)
        send_message(chat_id, "✅ Вы зарегистрированы! Теперь вы будете получать уведомления об оплате.")
    
    elif text == "/stats":
        total_users = len(user_data)
        registered_users = sum(1 for u in user_data.values() if u.get("registered"))
        send_message(chat_id, f"📊 Статистика:\nВсего пользователей: {total_users}\nЗарегистрировано: {registered_users}")
    
    elif text == "/remindme":
        # Устанавливаем напоминание на через 2 минуты (для теста)
        reminder_time = datetime.now() + timedelta(minutes=2)
        reminder_id = f"{user_id}_{datetime.now().timestamp()}"
        
        reminders[reminder_id] = {
            "user_id": user_id,
            "time": reminder_time.isoformat(),
            "message": "Тестовое напоминание об оплате"
        }
        save_data(REMINDERS_FILE, reminders)
        
        send_message(chat_id, f"⏰ Напоминание установлено на {reminder_time.strftime('%H:%M')}")
    
    elif text:
        send_message(chat_id, "🤖 Я получил ваше сообщение! Используй /help для списка команд.")

def main():
    logger.info("🚀 Запуск бота с системой напоминаний...")
    logger.info(f"📞 Токен: {BOT_TOKEN[:10]}...")
    
    # Создаем папки если их нет
    os.makedirs("data", exist_ok=True)
    
    offset = None
    last_reminder_check = time.time()
    
    try:
        while True:
            current_time = time.time()
            
            # Проверяем напоминания каждые 30 секунд
            if current_time - last_reminder_check > 30:
                check_reminders()
                last_reminder_check = current_time
            
            # Получаем новые сообщения
            updates = get_updates(offset)
            
            if updates.get("ok"):
                for update in updates["result"]:
                    if "message" in update:
                        handle_message(update["message"])
                        offset = update["update_id"] + 1
            
            # Короткая пауза перед следующей проверкой
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка бота...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()