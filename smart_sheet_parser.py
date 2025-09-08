# smart_sheet_parser.py
import gspread
import re
import os  # Добавляем импорт os
from google.oauth2.service_account import Credentials

class SmartSheetParser:
    def __init__(self, spreadsheet_id: str, sheet_name: str, service_account_key: str):
        self.worksheet = None
        self.fio_column = 1
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.service_account_key = service_account_key
        self.setup_google_sheets()
        
    def setup_google_sheets(self):
        """Настраивает подключение к Google Sheets"""
        try:
            if not os.path.exists(self.service_account_key):
                print("❌ Файл ключа сервисного аккаунта не найден")
                return
                
            creds = Credentials.from_service_account_file(
                self.service_account_key,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            gc = gspread.authorize(creds)
            self.worksheet = gc.open_by_key(self.spreadsheet_id).worksheet(self.sheet_name)
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