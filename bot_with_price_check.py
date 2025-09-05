# Добавьте в начало файла
def is_price_valid(price_str):
    """Проверяет что цена валидна и выставлена"""
    if not price_str or not isinstance(price_str, str):
        return False
        
    # Очищаем строку от пробелов
    clean_price = price_str.strip()
    
    # Проверяем пустые значения и нули
    if not clean_price or clean_price in ['0', '0.0', '0,0', '-', '']:
        return False
        
    try:
        # Заменяем запятые на точки и преобразуем в число
        price = float(clean_price.replace(',', '.'))
        # Цена должна быть положительной
        return price > 0
    except (ValueError, TypeError):
        return False

# Затем в функции check_orders_and_notify:
for order in orders:
    if order['has_order'] and is_price_valid(order['price']):
        # Отправляем уведомление
        print(f"✅ Цена валидна: {order['fio']} - {order['price']} руб.")
    elif order['has_order']:
        print(f"⏳ Ожидание цены: {order['fio']}")