import gspread
from google.oauth2.service_account import Credentials

def test_google_sheets():
    try:
        # Настройки
        SPREADSHEET_ID = "1B_u7XNX-tWurpxrHgQdJuFWWTwP3KW8kX7_VyuQzJwY"
        CREDS_FILE = "credentials/service_account_key.json"
        
        print("🔍 Проверка подключения к Google Sheets...")
        
        # Проверяем существование файла credentials
        import os
        if not os.path.exists(CREDS_FILE):
            print("❌ Файл credentials не найден!")
            print("📍 Положите service_account_key.json в папку credentials/")
            return False
        
        print("✅ Файл credentials найден")
        
        # Пытаемся подключиться
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
        gc = gspread.authorize(creds)
        
        print("✅ Успешная авторизация в Google API")
        
        # Пытаемся открыть таблицу
        try:
            spreadsheet = gc.open_by_key(SPREADSHEET_ID)
            print("✅ Таблица найдена!")
            
            # Получаем данные из листа
            worksheet = spreadsheet.worksheet("Меню")
            data = worksheet.get_all_values()
            
            print(f"📊 Найдено строк: {len(data)}")
            
            # Показываем заголовки
            if len(data) > 0:
                print("📋 Заголовки столбцов:")
                headers = data[0]
                for i, header in enumerate(headers):
                    print(f"   {i+1}. {header}")
            
            # Показываем первые 5 заказов
            if len(data) > 1:
                print("\n📦 Первые заказы:")
                for i, row in enumerate(data[1:6], 1):  # первые 5 строк после заголовка
                    if row[0]:  # если есть ФИО
                        print(f"   {i}. {row[0]} - {row[1] if len(row)>1 else ''}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка доступа к таблице: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

if __name__ == "__main__":
    test_google_sheets()
    input("\nНажмите Enter для выхода...")