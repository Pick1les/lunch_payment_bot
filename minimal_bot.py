import logging
import requests
import time

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8246985665:AAGpHgRVwU3t8vHGwE1bfRxrGGgeJWwyAKA"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_updates(offset=None):
    """Получаем обновления от Telegram"""
    url = f"{API_URL}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    try:
        response = requests.get(url, params=params, timeout=110)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка получения updates: {e}")
        return {"ok": False}

def send_message(chat_id, text):
    """Отправляем сообщение"""
    url = f"{API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        return {"ok": False}

def process_update(update):
    """Обрабатываем обновление"""
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        
        if text == "/start":
            send_message(chat_id, "✅ Бот работает! Привет!")
        elif text == "/test":
            user = message["from"]
            send_message(chat_id, f"Тест пройден! 🚀\nID: {user['id']}\nИмя: {user['first_name']}")

def main():
    logger.info("🚀 Запуск простого бота...")
    offset = None
    
    while True:
        try:
            result = get_updates(offset)
            if result["ok"]:
                for update in result["result"]:
                    process_update(update)
                    offset = update["update_id"] + 1
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Остановка бота...")
            break
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()