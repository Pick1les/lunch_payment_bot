import requests
import os
import sys

try:
    from config import BOT_TOKEN
except ImportError:
    print("❌ Файл config.py не найден")
    sys.exit(1)

def check_bot_token():
    """Проверяет валидность токена бота"""
    if not BOT_TOKEN or BOT_TOKEN == "ВАШ_ТОКЕН_БОТА":
        print("❌ Токен бота не настроен в config.py")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Токен валиден!")
            print(f"🤖 Имя бота: {data['result']['first_name']}")
            print(f"🔗 Username: @{data['result']['username']}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.json())
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == '__main__':
    check_bot_token()
    input("\nНажмите Enter для выхода...")