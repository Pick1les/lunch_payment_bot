import requests
import time
import json
import os
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

# Ваш токен
BOT_TOKEN = "8246985665:AAGpHgRVwU3t8vHGwE1bfRxrGGgeJWwyAKA"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Настройки Google Sheets (замените на свои)
SPREADSHEET_ID = "https://docs.google.com/spreadsheets/d/1B_u7XNX-tWurpxrHgQdJuFWWTwP3KW8kX7_VyuQzJwY/edit?gid=394578358#gid=394578358"  # ID вашей таблицы
SHEET_NAME = "Лист1"  # Название листа

# Файлы для данных
USER_DATA_FILE = "user_data.json"

class GoogleSheetsManager:
    def __init__(self):
        self.worksheet = None
        self.setup_google_sheets()
        
    def setup_google_sheets(self):
        """Настройка подключения к Google Sheets"""
        try:
            creds_file = "credentials/service_account_key.json"
            if not os.path.exists(creds_file):
                print("❌ Файл с credentials не найден")
                print("📍 Положите service_account_key.json в папку credentials/")
                return
                
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
            gc = gspread.authorize(creds)
            self.worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
            print("✅ Успешное подключение к Google Sheets")
        except Exception as e:
            print(f"❌ Ошибка подключения к Google Sheets: {e}")

    def get_todays_orders(self):
        """Получает сегодняшние заказы из таблицы"""
        if not self.worksheet:
            return []
            
        try:
            # Получаем все данные
            all_data = self.worksheet.get_all_values()
            
            orders = []
            for row in all_data[1:]:  # пропускаем заголовок
                if len(row) > 0 and row[0].strip():  # если есть ФИО
                    order = {
                        'fio': row[0].strip(),
                        'dishes': [],
                        'has_order': False
                    }
                    
                    # Проверяем блюда (колонки 1-5)
                    dishes = []
                    for i in range(1, 6):
                        if len(row) > i and row[i].strip():
                            dishes.append(row[i].strip())
                    
                    if dishes:
                        order['dishes'] = dishes
                        order['has_order'] = True
                        order['price'] = row[7] if len(row) > 7 and row[7].strip() else "0"
                    
                    orders.append(order)
                    
            return orders
        except Exception as e:
            print(f"❌ Ошибка чтения Google Sheets: {e}")
            return []

def load_data():
    """Загружает данные пользователей"""
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_data(data):
    """Сохраняет данные"""
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except:
        pass

def send_message(chat_id, text):
    """Отправляет сообщение"""
    url = f"{API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

def get_updates(offset=None):
    """Получает новые сообщения"""
    url = f"{API_URL}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    try:
        response = requests.get(url, params=params, timeout=110)
        return response.json()
    except:
        return {"ok": False, "result": []}

def check_orders_and_notify(gs_manager, user_data):
    """Проверяет заказы и отправляет уведомления"""
    try:
        orders = gs_manager.get_todays_orders()
        print(f"📋 Найдено заказов: {len(orders)}")
        
        notified_users = set()
        
        for order in orders:
            if order['has_order']:
                # Ищем пользователя по ФИО
                for user_id, user_info in user_data.items():
                    if (user_info.get('registered') and 
                        user_info.get('fio') and 
                        user_info['fio'].lower() == order['fio'].lower()):
                        
                        # Формируем сообщение о заказе
                        message = "🍽️ *Ваш заказ на сегодня:*\n\n"
                        for dish in order['dishes']:
                            message += f"• {dish}\n"
                        
                        message += f"\n💵 Сумма: {order['price']} руб.\n"
                        message += "💳 Пожалуйста, оплатите до 14:00"
                        
                        send_message(user_id, message)
                        notified_users.add(user_id)
                        print(f"📨 Уведомление отправлено {order['fio']}")
                        break
        
        print(f"✅ Уведомления отправлены: {len(notified_users)} пользователям")
                        
    except Exception as e:
        print(f"❌ Ошибка проверки заказов: {e}")

def main():
    print("🚀 Бот запущен с Google Sheets!")
    print("📊 Отправьте /checkorders для проверки заказов")
    
    # Инициализируем Google Sheets
    gs_manager = GoogleSheetsManager()
    
    user_data = load_data()
    offset = None
    last_check = time.time()
    
    try:
        while True:
            current_time = time.time()
            
            # Автоматическая проверка заказов каждые 5 минут
            if current_time - last_check > 300:  # 5 минут
                check_orders_and_notify(gs_manager, user_data)
                last_check = current_time
            
            # Обработка сообщений
            updates = get_updates(offset)
            
            if updates.get("ok"):
                for update in updates["result"]:
                    if "message" in update:
                        message = update["message"]
                        chat_id = str(message["chat"]["id"])
                        text = message.get("text", "").strip()
                        user = message["from"]
                        
                        user_id = str(user["id"])
                        
                        # Инициализируем пользователя если его нет
                        if user_id not in user_data:
                            user_data[user_id] = {
                                "first_name": user.get("first_name", ""),
                                "username": user.get("username", ""),
                                "registered": False,
                                "fio": "",
                                "step": "start"
                            }
                        
                        # Обработка команд
                        if text == "/start":
                            send_message(chat_id, 
                                "👋 Привет! Я бот для напоминаний об оплате обедов!\n\n"
                                "Отправьте /register чтобы начать регистрацию"
                            )
                            user_data[user_id]["step"] = "start"
                            
                        elif text == "/register":
                            user_data[user_id]["registered"] = True
                            user_data[user_id]["step"] = "waiting_fio"
                            send_message(chat_id, 
                                "✅ Вы зарегистрированы!\n"
                                "📝 Теперь отправьте свои ФИО точно как в таблице заказов\n"
                                "Пример: Иванов Иван Иванович"
                            )
                            
                        elif text == "/myinfo":
                            info = user_data[user_id]
                            response = (
                                f"👤 Ваша информация:\n"
                                f"• ID: {user_id}\n"
                                f"• Имя: {info['first_name']}\n"
                                f"• ФИО: {info.get('fio', 'не указано')}\n"
                                f"• Статус: {'зарегистрирован' if info['registered'] else 'не зарегистрирован'}"
                            )
                            send_message(chat_id, response)
                            
                        elif text == "/checkorders":
                            orders = gs_manager.get_todays_orders()
                            active_orders = sum(1 for order in orders if order['has_order'])
                            send_message(chat_id, f"📊 Сегодняшних заказов: {active_orders}/{len(orders)}")
                            
                        elif user_data[user_id].get("step") == "waiting_fio":
                            # Пользователь отправляет ФИО после регистрации
                            user_data[user_id]["fio"] = text
                            user_data[user_id]["step"] = "completed"
                            send_message(chat_id, f"✅ ФИО сохранено: {text}")
                            
                        else:
                            send_message(chat_id, 
                                "🤖 Используйте команды:\n"
                                "/start - начать\n"
                                "/register - регистрация\n"  
                                "/myinfo - мои данные\n"
                                "/checkorders - проверить заказы"
                            )
                        
                        offset = update["update_id"] + 1
                        save_data(user_data)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("⏹️ Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()