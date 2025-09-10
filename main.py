import requests
import time
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

from config import Config, config
from security import DataEncryptor
from utils import setup_logging, load_data, save_data, create_backup, get_bot_stats
from validation import validate_fio, sanitize_input, is_price_valid
from smart_sheet_parser import SmartSheetParser

# Настраиваем логирование
setup_logging(config.LOG_FILE)
logger = logging.getLogger(__name__)

class LunchBot:
    def __init__(self):
        # Создаем шифровальщик
        self.encryptor = DataEncryptor(config.BOT_TOKEN)
        
        # Загружаем данные
        self.user_data = load_data(config.USER_DATA_FILE, self.encryptor)
        self.payments_data = load_data(config.PAYMENTS_FILE, self.encryptor)
        
        # Инициализируем парсер
        self.parser = SmartSheetParser(
            config.SPREADSHEET_ID,
            config.SHEET_NAME,
            config.SERVICE_ACCOUNT_KEY
        )
        
        self.offset = None
        
    def send_message(self, chat_id: int, text: str, reply_markup: Dict = None) -> bool:
        """Безопасно отправляет сообщение"""
        try:
            sanitized_text = sanitize_input(text)
            data = {
                "chat_id": chat_id,
                "text": sanitized_text,
                "parse_mode": "Markdown"
            }
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            
            response = requests.post(f"{config.API_URL}/sendMessage", data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            return False

    def get_payment_message(self, amount: str = None) -> str:
        """Возвращает сообщение с реквизитами"""
        payment_text = (
            "💳 *Реквизиты для перевода:*\n\n"
            f"🏦 Банк: {config.PAYMENT_DETAILS['bank']}\n"
            f"📞 Телефон: `{config.PAYMENT_DETAILS['phone']}`\n"
            f"👤 Получатель: {config.PAYMENT_DETAILS['name']}\n"
            f"📝 Комментарий: {config.PAYMENT_DETAILS['comment']}"
        )
        if amount and amount != '0':
            payment_text += f"\n💵 Сумма: {amount} руб."
        payment_text += "\n\n⚠️ Укажите комментарий к переводу!"
        return payment_text

    def format_order_message(self, order: Dict, notification_type: str = "auto") -> str:
        """Форматирует сообщение о заказе"""
        message = f"🍽️ *Заказ для {order['fio']}:*\n\n"
        
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
        
        message += f"\n💵 *Сумма: {order['price']} руб.*\n"
        
        if notification_type == "reminder":
            message += "⏰ *Напоминание:* оплатите до 14:00\n\n"
        elif notification_type == "urgent":
            message += "⚠️ *СРОЧНО:* последний шанс оплатить до 14:00!\n\n"
        else:
            message += "💳 Оплатите до 14:00\n\n"
        
        return message

    def create_payment_keyboard(self) -> Dict:
        """Создает клавиатуру для подтверждения оплаты"""
        return {
            "inline_keyboard": [[
                {
                    "text": "✅ Я оплатил(а)",
                    "callback_data": "payment_confirmed"
                }
            ]]
        }

    def create_admin_keyboard(self):
        """Создает клавиатуру для администратора"""
        return {
            "keyboard": [
                ["/stats", "/users"],
                ["/broadcast", "/backup"],
                ["/check_orders", "/notify_admin"],
                ["/main_menu"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }

    def create_main_keyboard(self):
        """Создает основную клавиатуру"""
        return {
            "keyboard": [
                ["/start", "/register"],
                ["/payment", "/checkorders"],
                ["/mystatus"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }

    def get_welcome_message(self) -> str:
        """Возвращает приветственное сообщение"""
        return (
            "👋 *Добро пожаловать в бот для оплаты обедов!*\n\n"
            "📋 *Список команд:*\n\n"
            "📍 */start* - показать это сообщение\n"
            "📍 */register* - регистрация в системе\n"
            "📍 */payment* - реквизиты для оплаты\n"
            "📍 */checkorders* - проверить сегодняшние заказы\n"
            "📍 */mystatus* - мой статус оплаты\n\n"
            "⚡ *Как это работает:*\n"
            "1. Регистрируетесь командой /register\n"
            "2. Указываете свои ФИО как в таблице\n"
            "3. Получаете уведомления о заказах\n"
            "4. Оплачиваете и нажимаете \"✅ Я оплатил\"\n\n"
            "💡 Бот автоматически проверяет заказы"
        )

    def should_send_notification(self) -> bool:
        """Проверяет, можно ли отправлять уведомления"""
        now = datetime.now()
        current_time = now.time()
        
        start_time = datetime.strptime(config.NOTIFICATION_SETTINGS['start_time'], "%H:%M").time()
        end_time = datetime.strptime(config.NOTIFICATION_SETTINGS['end_time'], "%H:%M").time()
        
        return start_time <= current_time <= end_time

    def get_current_notification_type(self) -> str:
        """Определяет тип уведомления по времени"""
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        
        if current_time_str == "11:30":
            return "reminder"
        elif current_time_str == "13:00":
            return "urgent"
        else:
            return "auto"

    def check_orders_and_notify(self):
        """Проверяет заказы и отправляет уведомления"""
        try:
            if not self.should_send_notification():
                logger.info("⏰ Сейчас не время для уведомлений")
                return
                
            orders = self.parser.get_todays_orders()
            notified_count = 0
            
            for order in orders:
                if order['has_order'] and is_price_valid(order['price']):
                    today = datetime.now().strftime("%Y-%m-%d")
                    order_key = f"{order['fio']}_{today}"
                    
                    # ПРОВЕРКА 1: ЕСЛИ УЖЕ ОПЛАЧЕНО - ПРОПУСКАЕМ ДЛЯ ВСЕХ ТИПОВ УВЕДОМЛЕНИЙ
                    if order_key in self.payments_data and self.payments_data[order_key].get('paid'):
                        logger.info(f"✅ Заказ уже оплачен: {order['fio']}")
                        continue
                    
                    notification_type = self.get_current_notification_type()
                    
                    # ПРОВЕРКА 2: ДЛЯ РАЗНЫХ ТИПОВ УВЕДОМЛЕНИЙ
                    if notification_type in ["reminder", "urgent"]:
                        # Для напоминаний проверяем, не отправляли ли уже ЭТОТ ТИП уведомления
                        if order_key in self.payments_data and self.payments_data[order_key].get('last_notification_type') == notification_type:
                            logger.info(f"⚠️ Уже отправляли {notification_type} для {order['fio']}")
                            continue
                    else:
                        # Для обычных уведомлений проверяем, отправляли ли вообще какое-либо уведомление
                        if order_key in self.payments_data:
                            logger.info(f"⚠️ Уведомление уже отправлено: {order['fio']}")
                            continue
                    
                    for user_id, user_info in self.user_data.items():
                        if (user_info.get('registered') and user_info.get('fio') and 
                            user_info['fio'].lower() == order['fio'].lower()):
                            
                            message = self.format_order_message(order, notification_type)
                            message += self.get_payment_message(order['price'])
                            
                            if self.send_message(user_id, message, self.create_payment_keyboard()):
                                if order_key not in self.payments_data:
                                    self.payments_data[order_key] = {
                                        "user_id": user_id,
                                        "fio": order['fio'],
                                        "amount": order['price'],
                                        "date": today,
                                        "paid": False,
                                        "notifications_sent": 0
                                    }
                                
                                self.payments_data[order_key]['last_notification_type'] = notification_type
                                self.payments_data[order_key]['last_notification_time'] = datetime.now().isoformat()
                                self.payments_data[order_key]['notifications_sent'] += 1
                                
                                notified_count += 1
                                logger.info(f"📨 Отправлен {notification_type} для {order['fio']} - {order['price']} руб.")
                            break
            
            save_data(config.PAYMENTS_FILE, self.payments_data, self.encryptor)
            logger.info(f"✅ Уведомления отправлены: {notified_count} пользователям")
                        
        except Exception as e:
            logger.error(f"❌ Ошибка проверки заказов: {e}")

    def handle_callback_query(self, update: Dict):
        """Обрабатывает callback-запросы"""
        try:
            query = update['callback_query']
            user_id = str(query['from']['id'])
            message = query['message']
            chat_id = message['chat']['id']
            message_id = message['message_id']
            
            if query['data'] == 'payment_confirmed':
                today = datetime.now().strftime("%Y-%m-%d")
                user_info = self.user_data.get(user_id, {})
                user_fio = user_info.get('fio', '')
                
                if user_fio:
                    order_key = f"{user_fio}_{today}"
                    if order_key in self.payments_data:
                        self.payments_data[order_key]['paid'] = True
                        self.payments_data[order_key]['paid_at'] = datetime.now().isoformat()
                        save_data(config.PAYMENTS_FILE, self.payments_data, self.encryptor)
                        
                        requests.post(f"{config.API_URL}/answerCallbackQuery", 
                                    data={"callback_query_id": query['id']})
                        
                        edit_text = message['text'] + "\n\n✅ *Оплата подтверждена!*"
                        requests.post(f"{config.API_URL}/editMessageText", 
                                    data={
                                        "chat_id": chat_id,
                                        "message_id": message_id,
                                        "text": edit_text,
                                        "parse_mode": "Markdown"
                                    })
                        
                        logger.info(f"✅ Подтверждена оплата: {user_fio}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки callback: {e}")

    def handle_stats_command(self, chat_id: int):
        """Обрабатывает команду статистики"""
        try:
            stats = get_bot_stats(self.user_data, self.payments_data)
            
            message = (
                "📊 *Статистика бота:*\n\n"
                f"👥 Всего пользователей: {stats['total_users']}\n"
                f"✅ Зарегистрировано: {stats['registered_users']}\n"
                f"📝 С ФИО: {stats['users_with_fio']}\n\n"
                f"🍽️ Заказов сегодня: {stats['today_orders']}\n"
                f"💳 Оплачено сегодня: {stats['today_paid']}\n\n"
                f"📦 Всего заказов: {stats['total_orders']}\n"
                f"💰 Всего оплат: {stats['total_paid']}\n\n"
                f"⏰ Время сервера: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            self.send_message(chat_id, message)
        except Exception as e:
            self.send_message(chat_id, f"❌ Ошибка получения статистики: {e}")

    def handle_users_command(self, chat_id: int):
        """Обрабатывает команду списка пользователей"""
        try:
            if not self.user_data:
                self.send_message(chat_id, "📝 Пользователей нет")
                return
                
            message = "👥 *Список пользователей:*\n\n"
            for i, (user_id, user_info) in enumerate(list(self.user_data.items())[:50], 1):
                status = "✅" if user_info.get('registered') else "❌"
                fio = user_info.get('fio', 'нет ФИО')
                username = user_info.get('username', 'нет username')
                message += f"{i}. {status} {fio} (@{username})\n"
                
            if len(self.user_data) > 50:
                message += f"\n... и еще {len(self.user_data) - 50} пользователей"
                
            self.send_message(chat_id, message)
        except Exception as e:
            self.send_message(chat_id, f"❌ Ошибка получения списка пользователей: {e}")

    def handle_broadcast_message(self, chat_id: int, message_text: str, admin_id: str):
        """Обрабатывает рассылку сообщения"""
        try:
            success_count = 0
            fail_count = 0
            
            for user_id, user_info in self.user_data.items():
                if user_id != admin_id and user_info.get('registered'):
                    if self.send_message(user_id, f"📢 *Рассылка от администратора:*\n\n{message_text}"):
                        success_count += 1
                    else:
                        fail_count += 1
                    time.sleep(0.1)  # Чтобы не превысить лимиты API
            
            report = (
                f"✅ Рассылка завершена!\n\n"
                f"📨 Отправлено: {success_count}\n"
                f"❌ Не отправлено: {fail_count}\n"
                f"👥 Всего пользователей: {len(self.user_data)}"
            )
            
            self.send_message(chat_id, report)
            self.user_data[admin_id]["step"] = None
            
        except Exception as e:
            self.send_message(chat_id, f"❌ Ошибка рассылки: {e}")
            self.user_data[admin_id]["step"] = None

    def handle_backup_command(self, chat_id: int):
        """Обрабатывает команду backup"""
        try:
            success, message = create_backup(self.encryptor)
            self.send_message(chat_id, message)
        except Exception as e:
            self.send_message(chat_id, f"❌ Ошибка создания backup: {e}")

    def handle_check_orders_command(self, chat_id: int):
        """Принудительная проверка заказов"""
        try:
            self.send_message(chat_id, "🔄 Принудительная проверка заказов...")
            self.check_orders_and_notify()
            self.send_message(chat_id, "✅ Проверка завершена")
        except Exception as e:
            self.send_message(chat_id, f"❌ Ошибка проверки: {e}")

    def handle_notify_admin_command(self, chat_id: int):
        """Отправляет уведомление всем админам"""
        try:
            admin_count = 0
            admin_names = []
            
            for user_id in self.user_data:
                if int(user_id) in config.ADMIN_USER_IDS:
                    user_info = self.user_data[user_id]
                    name = user_info.get('first_name', 'Администратор')
                    username = user_info.get('username', '')
                    
                    if self.send_message(user_id, f"👑 *Уведомление от администратора:*\n\nТестирование системы уведомлений"):
                        admin_count += 1
                        admin_names.append(f"{name} (@{username})" if username else name)
            
            report = f"✅ Уведомления отправлены {admin_count} администраторам:\n"
            for name in admin_names:
                report += f"• {name}\n"
            
            self.send_message(chat_id, report)
        except Exception as e:
            self.send_message(chat_id, f"❌ Ошибка отправки уведомлений: {e}")

    def send_admin_daily_report(self):
        """Отправляет ежедневный отчет администраторам"""
        try:
            stats = get_bot_stats(self.user_data, self.payments_data)
            today = datetime.now().strftime("%Y-%m-%d")
            
            message = (
                "📊 *Ежедневный отчет*\n\n"
                f"📅 Дата: {today}\n\n"
                f"👥 Всего пользователей: {stats['total_users']}\n"
                f"✅ Зарегистрировано: {stats['registered_users']}\n"
                f"🍽️ Заказов сегодня: {stats['today_orders']}\n"
                f"💳 Оплачено сегодня: {stats['today_paid']}\n\n"
                f"💰 Ожидают оплаты: {stats['today_orders'] - stats['today_paid']}\n"
                f"⏰ Время сервера: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            for user_id in self.user_data:
                if int(user_id) in config.ADMIN_USER_IDS:
                    self.send_message(user_id, message)
                    
        except Exception as e:
            logger.error(f"Ошибка отправки ежедневного отчета: {e}")

    def handle_message(self, update: Dict):
        """Обрабатывает входящие сообщения"""
        message = update["message"]
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "").strip()
        user = message["from"]
        
        user_id = str(user["id"])
        
        # Проверяем администратор
        is_admin = int(user_id) in config.ADMIN_USER_IDS
        
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "first_name": user.get("first_name", ""),
                "username": user.get("username", ""),
                "registered": False,
                "fio": "",
                "step": "start"
            }
        
        # Обработка команды /start для всех
        if text == "/start":
            if is_admin:
                self.send_message(chat_id, "👑 *Режим администратора активирован*", self.create_admin_keyboard())
            else:
                self.send_message(chat_id, "📋 Основное меню", self.create_main_keyboard())
            self.send_message(chat_id, self.get_welcome_message())
            save_data(config.USER_DATA_FILE, self.user_data, self.encryptor)
            return
        
        # Обработка команды /main_menu для всех
        elif text == "/main_menu":
            self.send_message(chat_id, "📋 Основное меню", self.create_main_keyboard())
            save_data(config.USER_DATA_FILE, self.user_data, self.encryptor)
            return
        
        # Обработка шага waiting_fio для всех
        elif self.user_data[user_id].get("step") == "waiting_fio":
            cleaned_fio = validate_fio(text)
            if cleaned_fio:
                self.user_data[user_id]["fio"] = cleaned_fio
                self.user_data[user_id]["step"] = "completed"
                self.send_message(chat_id, f"✅ ФИО сохранено: {cleaned_fio}")
                self.send_message(chat_id, "📩 Теперь вы будете получать уведомления о заказах!")
            else:
                self.send_message(chat_id, "❌ Неверный формат ФИО. Попробуйте еще раз.")
            save_data(config.USER_DATA_FILE, self.user_data, self.encryptor)
            return
        
        # Обработка шага waiting_broadcast только для админов
        elif self.user_data[user_id].get("step") == "waiting_broadcast":
            if is_admin:
                self.handle_broadcast_message(chat_id, text, user_id)
            else:
                self.user_data[user_id]["step"] = None
            save_data(config.USER_DATA_FILE, self.user_data, self.encryptor)
            return
        
        # АДМИН-КОМАНДЫ (только для администраторов)
        if is_admin:
            admin_commands_processed = False
            
            if text == "/stats":
                self.handle_stats_command(chat_id)
                admin_commands_processed = True
                
            elif text == "/users":
                self.handle_users_command(chat_id)
                admin_commands_processed = True
                
            elif text == "/broadcast":
                self.user_data[user_id]["step"] = "waiting_broadcast"
                self.send_message(chat_id, "📢 Введите сообщение для рассылки:")
                admin_commands_processed = True
                
            elif text == "/backup":
                self.handle_backup_command(chat_id)
                admin_commands_processed = True
                
            elif text == "/check_orders":
                self.handle_check_orders_command(chat_id)
                admin_commands_processed = True
                
            elif text == "/notify_admin":
                self.handle_notify_admin_command(chat_id)
                admin_commands_processed = True
            
            # Если админская команда обработана, сохраняем данные и выходим
            if admin_commands_processed:
                save_data(config.USER_DATA_FILE, self.user_data, self.encryptor)
                return
        
        # ОБЫЧНЫЕ КОМАНДЫ ПОЛЬЗОВАТЕЛЕЙ (для всех, включая администраторов)
        if text == "/register":
            self.user_data[user_id]["registered"] = True
            self.user_data[user_id]["step"] = "waiting_fio"
            self.send_message(chat_id, "✅ Вы зарегистрированы! Теперь отправьте ваше ФИО как в таблице заказов:")
            
        elif text == "/checkorders":
            if self.parser.worksheet:
                orders = self.parser.get_todays_orders()
                active_orders = [o for o in orders if o['has_order'] and is_price_valid(o['price'])]
                
                if active_orders:
                    self.send_message(chat_id, f"📊 Все заказы на сегодня: {len(active_orders)}")
                    
                    total_amount = 0.0
                    for order in active_orders:
                        order_info = f"👤 {order['fio']} - {order['price']} руб.\n"
                        
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
                        
                        self.send_message(chat_id, order_info)
                        
                        try:
                            price = float(order['price'].replace(',', '.'))
                            total_amount += price
                        except (ValueError, TypeError):
                            pass
                    
                    self.send_message(chat_id, f"💰 *Общая сумма всех заказов: {total_amount:.2f} руб.*")
                    
                else:
                    self.send_message(chat_id, "📊 На сегодня заказов нет")
            else:
                self.send_message(chat_id, "❌ Таблица не подключена")
            
        elif text == "/payment":
            self.send_message(chat_id, self.get_payment_message())
            
        elif text == "/mystatus":
            user_info = self.user_data.get(user_id, {})
            if user_info.get('fio'):
                today = datetime.now().strftime("%Y-%m-%d")
                order_key = f"{user_info['fio']}_{today}"
                
                # ПРОВЕРЯЕМ СНАЧАЛА ЗАКАЗЫ ИЗ ТАБЛИЦЫ
                orders = self.parser.get_todays_orders()
                user_has_order = any(order['fio'].lower() == user_info['fio'].lower() 
                                   for order in orders if order['has_order'])
                
                if not user_has_order:
                    self.send_message(chat_id, "📊 Заказа на сегодня нет")
                    return
                    
                # ЕСТЬ ЗАКАЗ - ПРОВЕРЯЕМ СТАТУС ОПЛАТЫ
                if order_key in self.payments_data:
                    status = "✅ Оплачено" if self.payments_data[order_key]['paid'] else "❌ Не оплачено"
                    amount = self.payments_data[order_key]['amount']
                    notifications = self.payments_data[order_key].get('notifications_sent', 0)
                    self.send_message(chat_id, f"📊 Ваш статус: {status}\n💵 Сумма: {amount} руб.\n📨 Уведомлений: {notifications}")
                else:
                    # ЗАКАЗ ЕСТЬ, НО ОПЛАТА ЕЩЕ НЕ ОБРАБОТАНА
                    order_info = next((order for order in orders 
                                     if order['fio'].lower() == user_info['fio'].lower() 
                                     and order['has_order']), None)
                    if order_info:
                        self.send_message(chat_id, 
                            f"📊 Заказ есть!\n"
                            f"💵 Сумма: {order_info['price']} руб.\n"
                            f"📝 Статус: Ожидает оплаты\n\n"
                            f"💳 Используйте /payment для реквизитов")
            else:
                self.send_message(chat_id, "❌ Сначала зарегистрируйтесь /register")
            
        else:
            self.send_message(chat_id, "🤖 Неизвестная команда. Используйте /start для списка команд")
        
        save_data(config.USER_DATA_FILE, self.user_data, self.encryptor)

    def run(self):
        """Основной цикл бота"""
        logger.info("🚀 Безопасный бот запущен!")
        logger.info(f"⏰ Время уведомлений: {config.NOTIFICATION_SETTINGS['start_time']}-{config.NOTIFICATION_SETTINGS['end_time']}")
        logger.info(f"👑 Администраторы: {config.ADMIN_USER_IDS}")
        
        last_check = time.time()
        last_reminder_check = time.time()
        last_admin_notification = time.time()
        last_backup = time.time()
        
        try:
            while True:
                current_time = time.time()
                current_time_str = datetime.now().strftime("%H:%M")
                
                # Проверяем заказы каждые 5 минут
                if current_time - last_check > config.NOTIFICATION_SETTINGS['check_interval']:
                    self.check_orders_and_notify()
                    last_check = current_time
                
                # Проверяем время напоминаний каждую минуту
                if current_time - last_reminder_check > 60:
                    if current_time_str in config.NOTIFICATION_SETTINGS['reminder_times']:
                        logger.info(f"🔔 Время для напоминания: {current_time_str}")
                        self.check_orders_and_notify()
                    last_reminder_check = current_time
                
                # Ежедневное уведомление админам
                if current_time - last_admin_notification > 3600:
                    if current_time_str == config.ADMIN_NOTIFICATION_TIME:
                        self.send_admin_daily_report()
                        last_admin_notification = current_time
                
                # Ежедневный backup
                if current_time - last_backup > 3600:
                    if current_time_str == config.BACKUP_TIME:
                        success, message = create_backup(self.encryptor)
                        logger.info(f"Автоматический backup: {message}")
                        last_backup = current_time
                
                # Обрабатываем сообщения
                try:
                    response = requests.get(f"{config.API_URL}/getUpdates", 
                                        params={"timeout": 100, "offset": self.offset}).json()
                    
                    if response.get("ok"):
                        for update in response["result"]:
                            if "callback_query" in update:
                                self.handle_callback_query(update)
                                self.offset = update['update_id'] + 1
                            
                            elif "message" in update:
                                self.handle_message(update)
                                self.offset = update['update_id'] + 1
                
                except Exception as e:
                    logger.error(f"Ошибка обработки обновлений: {e}")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Бот остановлен")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            # Гарантированно сохраняем данные при выходе
            save_data(config.USER_DATA_FILE, self.user_data, self.encryptor)
            save_data(config.PAYMENTS_FILE, self.payments_data, self.encryptor)

def main():
    """Главная функция"""
    try:
        bot = LunchBot()
        bot.run()
    except Exception as e:
        logger.critical(f"Не удалось запустить бота: {e}")

if __name__ == "__main__":
    main()