import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Логгер будет настроен в main
logger = logging.getLogger(__name__)

def load_data(filename: str, encryptor) -> Dict[str, Any]:
    """Безопасно загружает зашифрованные данные"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                encrypted_content = f.read()
                if encrypted_content:
                    return encryptor.decrypt_data(encrypted_content)
        return {}
    except Exception as e:
        logger.error(f"Ошибка загрузки данных из {filename}: {e}")
        return {}

def save_data(filename: str, data: Dict[str, Any], encryptor) -> bool:
    """Безопасно сохраняет зашифрованные данные"""
    try:
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        encrypted_data = encryptor.encrypt_data(data)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(encrypted_data)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения данных в {filename}: {e}")
        return False

def setup_logging(log_file: str):
    """Настраивает логирование"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def create_backup(encryptor, backup_dir: str = "backups"):
    """Создает backup данных"""
    try:
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Backup user data
        user_data = load_data("user_data.enc", encryptor)
        backup_file = os.path.join(backup_dir, f"user_data_backup_{timestamp}.json")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, indent=4, ensure_ascii=False)
        
        # Backup payments data
        payments_data = load_data("payments.enc", encryptor)
        backup_file = os.path.join(backup_dir, f"payments_backup_{timestamp}.json")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(payments_data, f, indent=4, ensure_ascii=False)
        
        return True, f"✅ Backup создан: {timestamp}"
    except Exception as e:
        return False, f"❌ Ошибка backup: {e}"

def get_bot_stats(user_data, payments_data):
    """Возвращает статистику бота"""
    try:
        total_users = len(user_data)
        registered_users = len([u for u in user_data.values() if u.get('registered')])
        users_with_fio = len([u for u in user_data.values() if u.get('fio')])
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_orders = len([p for p in payments_data.values() if p.get('date') == today])
        today_paid = len([p for p in payments_data.values() if p.get('date') == today and p.get('paid')])
        
        total_orders = len(payments_data)
        total_paid = len([p for p in payments_data.values() if p.get('paid')])
        
        return {
            'total_users': total_users,
            'registered_users': registered_users,
            'users_with_fio': users_with_fio,
            'today_orders': today_orders,
            'today_paid': today_paid,
            'total_orders': total_orders,
            'total_paid': total_paid
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return {}