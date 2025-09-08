# validation.py
import re
from typing import Optional

def validate_fio(fio: str) -> Optional[str]:
    """Проверяет и очищает ФИО"""
    if not fio or len(fio) > 100:
        return None
    
    cleaned_fio = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s\-\.]', '', fio.strip())
    return cleaned_fio if cleaned_fio else None

def validate_phone(phone: str) -> Optional[str]:
    """Проверяет номер телефона"""
    if not phone:
        return None
    
    cleaned_phone = re.sub(r'[^\d+]', '', phone)
    if cleaned_phone.startswith('+') and len(cleaned_phone) == 12:
        return cleaned_phone
    elif len(cleaned_phone) == 11:
        return '+7' + cleaned_phone[1:]
    return None

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Очищает пользовательский ввод"""
    if not text:
        return ""
    
    sanitized = re.sub(r'[<>{}`]', '', text)
    return sanitized[:max_length]

def is_price_valid(price_str: str) -> bool:
    """Проверяет валидность цены"""
    if not price_str:
        return False
        
    try:
        price = float(price_str.replace(',', '.'))
        return price > 0
    except (ValueError, TypeError):
        return False