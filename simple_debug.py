import gspread
from google.oauth2.service_account import Credentials

# Простейшая проверка
try:
    creds = Credentials.from_service_account_file("credentials/service_account_key.json", 
                scopes=["https://www.googleapis.com/auth/spreadsheets"])
    gc = gspread.authorize(creds)
    
    # Пробуем открыть таблицу
    spreadsheet = gc.open_by_key("1B_u7XNX-tWurpxrHgQdJuFWWTwP3KW8kX7_VyuQzJwY")
    print("✅ Таблица открыта успешно!")
    
    # Показываем все листы
    print("📋 Доступные листы:")
    for sheet in spreadsheet.worksheets():
        print(f"   - '{sheet.title}'")
        
    # Пробуем открыть лист "Меню"
    try:
        worksheet = spreadsheet.worksheet("Меню")
        print("✅ Лист 'Меню' найден!")
        
        # Показываем немного данных
        data = worksheet.get_all_values()
        print(f"📊 Строк в листе: {len(data)}")
        if data:
            print(f"📋 Заголовки: {data[0]}")
            
    except gspread.WorksheetNotFound:
        print("❌ Лист 'Меню' не найден!")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")

input("Нажмите Enter для выхода...")