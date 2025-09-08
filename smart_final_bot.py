import requests
import time
import json
import os
import gspread
import re
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

# Конфигурация
BOT_TOKEN = "8246985665:AAGpHgRVwU3t8vHGwE1bfRxrGGgeJWwyAKA"
SPREADSHEET_ID = "1B_u7XNX-tWurpxrHgQdJuFWWTwP3KW8kX7_VyuQzJwY"
SHEET_NAME = "Меню"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Настройки уведомлений
NOTIFICATION_SETTINGS = {
    'start_time': "10:20",
    'end_time': "14:00",
    'reminder_times': ["11:30", "13:00"],  # Фиксированное время напоминаний
    'check_interval': 300  # 5 минут
}

# Реквизиты
PAYMENT_DETAILS = {
    "bank": "Сбербанк",
    "phone": "+79604431441", 
    "name": "Александр Владимирович Е.",
    "comment": "Оплата обеда"
}

# Файлы данных
USER_DATA_FILE = "user_data.json"
PAYMENTS_FILE = "payments.json"

class SmartSheetParser:
    def __init__(self):
        self.worksheet = None
        self.fio_column = 1
        self.setup_google_sheets()
        
    def setup_google_sheets(self):
        """Настройка подключения к Google Sheets"""
        try:
            creds = Credentials.from_service_account_file("credentials/service_account_key.json", 
                        scopes=["https://www.googleapis.com/auth/spreadsheets"])
            gc = gspread.authorize(creds)
            self.worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
            print("✅ Успешное подключение к Google Sheets")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")

    def parse_order_row(self, row):
        """Парсит одну строку заказа"""
        if len(row) <= self.fio_column:
            return None
            
        fio = row[self.fio_column].strip()
        if not fio or fio.lower() in ['фио', 'фам', 'имя', 'итого', 'всего', '']:
            return None
        
        order_data = {
            'fio': fio,
            'first_dish': '',
            'second_dish': '',
            'garnish': '',
            'salad': '',
            'sauce': '',
            'comment': '',
            'price': '0'
        }
        
        for col_idx, cell in enumerate(row):
            if col_idx == self.fio_column:
                continue
                
            cell_value = cell.strip()
            if not cell_value:
                continue
                
            # Поиск цены
            price_match = re.search(r'(\d+[\d,.]*)', cell_value)
            if price_match:
                order_data['price'] = price_match.group(1)
                continue
                
            # Определяем тип ячейки по позиции
            if col_idx == 2:
                order_data['first_dish'] = cell_value
            elif col_idx == 3:
                order_data['second_dish'] = cell_value
            elif col_idx == 4:
                order_data['garnish'] = cell_value
            elif col_idx == 5:
                order_data['salad'] = cell_value
            elif col_idx == 6:
                order_data['sauce'] = cell_value
            elif col_idx == 7:
                order_data['comment'] = cell_value
        
        return order_data

    def get_todays_orders(self):
        """Получает и объединяет заказы"""
        if not self.worksheet:
            return []
            
        try:
            all_data = self.worksheet.get_all_values()
            if not all_data or len(all_data) < 3:
                return []
            
            orders_dict = {}
            
            for row in all_data[3:]:
                order_data = self.parse_order_row(row)
                if not order_data:
                    continue
                
                fio = order_data['fio']
                
                if fio in orders_dict:
                    existing_order = orders_dict[fio]
                    # Объединяем блюда
                    for key in ['first_dish', 'second_dish', 'garnish', 'salad', 'sauce']:
                        if order_data[key] and not existing_order[key]:
                            existing_order[key] = order_data[key]
                        elif order_data[key] and existing_order[key]:
                            existing_order[key] += f", {order_data[key]}"
                    
                    # Объединяем комментарии
                    if order_data['comment']:
                        if existing_order['comment']:
                            existing_order['comment'] += f"; {order_data['comment']}"
                        else:
                            existing_order['comment'] = order_data['comment']
                    
                    # Суммируем цены
                    try:
                        existing_price = float(existing_order['price'].replace(',', '.'))
                        new_price = float(order_data['price'].replace(',', '.'))
                        existing_order['price'] = str(round(existing_price + new_price, 2))
                    except:
                        pass
                else:
                    orders_dict[fio] = order_data
            
            orders = list(orders_dict.values())
            valid_orders = []
            
            for order in orders:
                has_dishes = any(order[key] for key in ['first_dish', 'second_dish', 'garnish', 'salad', 'sauce'])
                if has_dishes:
                    order['has_order'] = True
                    valid_orders.append(order)
                    print(f"📦 Заказ: {order['fio']} - {order['price']} руб.")
            
            print(f"✅ Найдено заказов: {len(valid_orders)}")
            return valid_orders
            
        except Exception as e:
            print(f"❌ Ошибка парсинга: {e}")
            return []

def load_data(filename):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_data(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except:
        pass

def send_message(chat_id, text, reply_markup=None):
    try:
        data = {"chat_id": chat_id, "text": text}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        requests.post(f"{API_URL}/sendMessage", data=data, timeout=10)
    except Exception as e:
        print(f"⚠️ Ошибка отправки сообщения: {e}")

def get_payment_message(amount=None):
    payment_text = (
        "💳 *Реквизиты для перевода:*\n\n"
        f"🏦 Банк: {PAYMENT_DETAILS['bank']}\n"
        f"📞 Телефон: `{PAYMENT_DETAILS['phone']}`\n"
        f"👤 Получатель: {PAYMENT_DETAILS['name']}\n"
        f"📝 Комментарий: {PAYMENT_DETAILS['comment']}"
    )
    if amount and amount != '0':
        payment_text += f"\n💵 Сумма: {amount} руб."
    payment_text += "\n\n⚠️ Укажите комментарий к переводу!"
    return payment_text

def format_order_message(order, notification_type="auto"):
    """Форматирует сообщение о заказе с учетом типа уведомления"""
    message = f"🍽️ *Заказ для {order['fio']}:*\n\n"
    
    # Добавляем все компоненты в правильном порядке
    components = [
        ("Первое", order['first_dish']),
        ("Второе", order['second_dish']),
        ("Гарнир", order['garnish']),
        ("Салат", order['salad']),
        ("Соус", order['sauce']),
        ("Комментарий", order['comment'])
    ]
    
    for name, value in components:
        if value:
            message += f"• *{name}:* {value}\n"
    
    # Добавляем сумму
    message += f"\n💵 *Сумма: {order['price']} руб.*\n"
    
    # Добавляем текст в зависимости от типа уведомления
    if notification_type == "reminder":
        message += "⏰ *Напоминание:* оплатите до 14:00\n\n"
    elif notification_type == "urgent":
        message += "⚠️ *СРОЧНО:* последний шанс оплатить до 14:00!\n\n"
    else:
        message += "💳 Оплатите до 14:00\n\n"
    
    return message

def create_payment_keyboard():
    """Создает клавиатуру для подтверждения оплаты"""
    return {
        "inline_keyboard": [[
            {
                "text": "✅ Я оплатил(а)",
                "callback_data": "payment_confirmed"
            }
        ]]
    }

def get_welcome_message():
    """Возвращает приветственное сообщение со списком команд"""
    return (
        "👋 *Добро пожаловать в бот для оплаты обедов!*\n\n"
        "📋 *Список команд:*\n\n"
        "📍 */start* - показать это сообщение\n"
        "📍 */register* - регистрация в системе\n"
        "📍 */payment* - реквизиты для оплата\n"
        "📍 */checkorders* - проверить сегодняшние заказы\n"
        "📍 */mystatus* - мой статус оплаты\n\n"
        "⚡ *Как это работает:*\n"
        "1. Регистрируетесь командой /register\n"
        "2. Указываете свои ФИО как в таблице\n"
        "3. Получаете уведомления о заказах\n"
        "4. Оплачиваете и нажимаете \"✅ Я оплатил\"\n\n"
        "💡 Бот автоматически проверяет заказы"
    )

def should_send_notification():
    """Проверяет, можно ли отправлять уведомления в текущее время"""
    now = datetime.now()
    current_time = now.time()
    
    # Отправляем уведомления только между 10:20 и 14:00
    start_time = datetime.strptime("10:20", "%H:%M").time()
    end_time = datetime.strptime("14:00", "%H:%M").time()
    
    return start_time <= current_time <= end_time

def is_price_valid(price_str):
    """Проверяет что цена валидна и выставлена"""
    if not price_str:
        return False
        
    try:
        # Заменяем запятые на точки и преобразуем в число
        price = float(price_str.replace(',', '.'))
        # Цена должна быть больше 0
        return price > 0
    except (ValueError, TypeError):
        return False

def get_current_notification_type():
    """Определяет тип уведомления based on current time"""
    now = datetime.now()
    current_time_str = now.strftime("%H:%M")
    
    if current_time_str == "11:30":
        return "reminder"
    elif current_time_str == "13:00":
        return "urgent"
    else:
        return "auto"

def check_orders_and_notify(parser, user_data, payments_data):
    """Проверяет заказы и отправляет уведомления с учетом типа"""
    try:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M:%S")
        notification_type = get_current_notification_type()
        
        print(f"⏰ Проверка в: {current_time_str}, тип: {notification_type}")
        
        # Проверяем время перед отправкой уведомлений
        if not should_send_notification():
            print("⏰ Сейчас не время для уведомлений")
            return
            
        orders = parser.get_todays_orders()
        notified_count = 0
        
        for order in orders:
            # Проверяем что заказ существует И цена выставлена
            if (order['has_order'] and is_price_valid(order['price'])):
                
                today = datetime.now().strftime("%Y-%m-%d")
                order_key = f"{order['fio']}_{today}"
                
                if order_key in payments_data and payments_data[order_key].get('paid'):
                    print(f"✅ Заказ уже оплачен, пропускаем: {order['fio']}")
                    continue
                
                # Для фиксированных напоминаний проверяем, не отправляли ли уже этот тип
                if notification_type in ["reminder", "urgent"]:
                    if order_key in payments_data and payments_data[order_key].get('last_notification_type') == notification_type:
                        print(f"⚠️ Уже отправляли {notification_type} для {order['fio']}")
                        continue
                
                # Для авто-уведомлений проверяем общую отправку
                elif order_key in payments_data:
                    print(f"⚠️ Уведомление уже отправлено: {order['fio']}")
                    continue
                
                # Ищем пользователя по ФИО
                for user_id, user_info in user_data.items():
                    if (user_info.get('registered') and 
                        user_info.get('fio') and 
                        user_info['fio'].lower() == order['fio'].lower()):
                        
                        # Формируем сообщение с учетом типа
                        message = format_order_message(order, notification_type)
                        message += get_payment_message(order['price'])
                        
                        # Отправляем с кнопкой подтверждения
                        send_message(user_id, message, create_payment_keyboard())
                        
                        # Сохраняем факт отправки уведомления
                        if order_key not in payments_data:
                            payments_data[order_key] = {
                                "user_id": user_id,
                                "fio": order['fio'],
                                "amount": order['price'],
                                "date": today,
                                "paid": False,
                                "notifications_sent": 0
                            }
                        
                        payments_data[order_key]['last_notification_type'] = notification_type
                        payments_data[order_key]['last_notification_time'] = now.isoformat()
                        payments_data[order_key]['notifications_sent'] += 1
                        
                        notified_count += 1
                        print(f"📨 Отправлен {notification_type} для {order['fio']} - {order['price']} руб.")
                        break
            
            elif order['has_order'] and (not is_price_valid(order['price'])):
                print(f"⏳ Заказ без цены: {order['fio']} - ожидание выставления цены")
        
        save_data(PAYMENTS_FILE, payments_data)
        print(f"✅ Уведомления отправлены: {notified_count} пользователям")
                        
    except Exception as e:
        print(f"❌ Ошибка проверки заказов: {e}")

def handle_callback_query(update, user_data, payments_data):
    """Обрабатывает нажатия на inline-кнопки"""
    try:
        query = update['callback_query']
        user_id = str(query['from']['id'])
        message = query['message']
        chat_id = message['chat']['id']
        message_id = message['message_id']
        
        if query['data'] == 'payment_confirmed':
            # Находим запись об оплате
            today = datetime.now().strftime("%Y-%m-%d")
            user_info = user_data.get(user_id, {})
            user_fio = user_info.get('fio', '')
            
            if user_fio:
                order_key = f"{user_fio}_{today}"
                if order_key in payments_data:
                    payments_data[order_key]['paid'] = True
                    payments_data[order_key]['paid_at'] = datetime.now().isoformat()
                    save_data(PAYMENTS_FILE, payments_data)
                    
                    # Отправляем подтверждение
                    requests.post(f"{API_URL}/answerCallbackQuery", 
                                data={"callback_query_id": query['id']})
                    
                    # Редактируем сообщение
                    edit_text = message['text'] + "\n\n✅ *Оплата подтверждена!*"
                    requests.post(f"{API_URL}/editMessageText", 
                                data={
                                    "chat_id": chat_id,
                                    "message_id": message_id,
                                    "text": edit_text,
                                    "parse_mode": "Markdown"
                                })
                    
                    print(f"✅ Подтверждена оплата: {user_fio}")
            
    except Exception as e:
        print(f"❌ Ошибка обработки callback: {e}")

def main():
    print("🚀 Умный бот запущен! С улучшенной системой уведомлений.")
    print(f"⏰ Время уведомлений: {NOTIFICATION_SETTINGS['start_time']}-{NOTIFICATION_SETTINGS['end_time']}")
    print(f"🔔 Напоминания в: {', '.join(NOTIFICATION_SETTINGS['reminder_times'])}")
    
    # Инициализируем парсер
    parser = SmartSheetParser()
    user_data = load_data(USER_DATA_FILE)
    payments_data = load_data(PAYMENTS_FILE)
    
    # Создаем файлы если их нет
    if not os.path.exists(USER_DATA_FILE):
        save_data(USER_DATA_FILE, {})
    if not os.path.exists(PAYMENTS_FILE):
        save_data(PAYMENTS_FILE, {})
    
    offset = None
    last_check = time.time()
    last_reminder_check = time.time()
    
    try:
        while True:
            current_time = time.time()
            now = datetime.now()
            current_time_str = now.strftime("%H:%M")
            
            # Проверяем заказы каждые 5 минут
            if current_time - last_check > NOTIFICATION_SETTINGS['check_interval'] and parser.worksheet:
                check_orders_and_notify(parser, user_data, payments_data)
                last_check = current_time
            
            # Отдельная проверка для фиксированных напоминаний
            if current_time - last_reminder_check > 60:  # Проверяем каждую минуту
                if current_time_str in NOTIFICATION_SETTINGS['reminder_times']:
                    print(f"🔔 Время для напоминания: {current_time_str}")
                    check_orders_and_notify(parser, user_data, payments_data)
                last_reminder_check = current_time
            
            # Обработка сообщений и callback-ов
            response = requests.get(f"{API_URL}/getUpdates", 
                                params={"timeout": 100, "offset": offset}).json()
            
            if response.get("ok"):
                for update in response["result"]:
                    # Обработка callback-ов (нажатий на кнопки)
                    if "callback_query" in update:
                        handle_callback_query(update, user_data, payments_data)
                        offset = update['update_id'] + 1
                    
                    # Обработка обычных сообщений
                    elif "message" in update:
                        message = update["message"]
                        chat_id = str(message["chat"]["id"])
                        text = message.get("text", "").strip()
                        user = message["from"]
                        
                        user_id = str(user["id"])
                        
                        if user_id not in user_data:
                            user_data[user_id] = {
                                "first_name": user.get("first_name", ""),
                                "username": user.get("username", ""),
                                "registered": False,
                                "fio": "",
                                "step": "start"
                            }
                        
                        if text == "/start":
                            send_message(chat_id, get_welcome_message())
                            
                        elif text == "/register":
                            user_data[user_id]["registered"] = True
                            user_data[user_id]["step"] = "waiting_fio"
                            send_message(chat_id, "✅ Вы зарегистрированы! Теперь отправьте ваше ФИО как в таблице заказов:")
                            
                        elif text == "/checkorders":
                            if parser.worksheet:
                                orders = parser.get_todays_orders()
                                active_orders = [o for o in orders if o['has_order'] and is_price_valid(o['price'])]
                                total_orders = len(orders)
                                
                                if active_orders:
                                    # Сначала отправляем общую статистику
                                    send_message(chat_id, f"📊 Все заказы на сегодня: {len(active_orders)}/{total_orders}")
                                    
                                    # Затем отправляем каждый заказ отдельным сообщением
                                    for order in active_orders:
                                        order_info = f"👤 {order['fio']} - {order['price']} руб.\n"
                                        
                                        # Добавляем информацию о блюдах
                                        if order.get('first_dish'):
                                            order_info += f"🥣 Первое: {order['first_dish']}\n"
                                        if order.get('second_dish'):
                                            order_info += f"🍖 Второе: {order['second_dish']}\n"
                                        if order.get('garnish'):
                                            order_info += f"🍚 Гарнир: {order['garnish']}\n"
                                        if order.get('salad'):
                                            order_info += f"🥗 Салат: {order['salad']}\n"
                                        if order.get('comment'):
                                            order_info += f"📝 Комментарий: {order['comment']}\n"
                                        
                                        send_message(chat_id, order_info)
                                        
                                        # Небольшая пауза между сообщениями
                                        time.sleep(0.5)
                                else:
                                    send_message(chat_id, "📊 На сегодня заказов нет")
                            else:
                                send_message(chat_id, "❌ Таблица не подключена")
                            
                        elif text == "/payment":
                            send_message(chat_id, get_payment_message())
                            
                        elif text == "/mystatus":
                            user_info = user_data.get(user_id, {})
                            if user_info.get('fio'):
                                today = datetime.now().strftime("%Y-%m-%d")
                                order_key = f"{user_info['fio']}_{today}"
                                if order_key in payments_data:
                                    status = "✅ Оплачено" if payments_data[order_key]['paid'] else "❌ Не оплачено"
                                    amount = payments_data[order_key]['amount']
                                    notifications = payments_data[order_key].get('notifications_sent', 0)
                                    send_message(chat_id, f"📊 Ваш статус: {status}\n💵 Сумма: {amount} руб.\n📨 Уведомлений: {notifications}")
                                else:
                                    send_message(chat_id, "📊 Заказа на сегодня нет")
                            else:
                                send_message(chat_id, "❌ Сначала зарегистрируйтесь /register")
                            
                        elif user_data[user_id].get("step") == "waiting_fio":
                            user_data[user_id]["fio"] = text
                            user_data[user_id]["step"] = "completed"
                            send_message(chat_id, f"✅ ФИО сохранено: {text}")
                            send_message(chat_id, "📩 Теперь вы будете получать уведомления о заказах!")
                            
                        else:
                            send_message(chat_id, "🤖 Неизвестная команда. Используйте /start для списка команд")
                        
                        offset = update['update_id'] + 1
                        save_data(USER_DATA_FILE, user_data)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("⏹️ Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()