# security.py
import json
from cryptography.fernet import Fernet
import base64
import os
from typing import Any, Dict

class DataEncryptor:
    def __init__(self, bot_token: str):
        self.key = self._generate_key(bot_token)
        self.cipher = Fernet(self.key)
    
    def _generate_key(self, bot_token: str) -> bytes:
        """Генерирует ключ шифрования на основе BOT_TOKEN"""
        if not bot_token:
            raise ValueError("BOT_TOKEN is required for encryption")
        
        key_base = bot_token[:32].ljust(32, '0')[:32]
        return base64.urlsafe_b64encode(key_base.encode())
    
    def encrypt_data(self, data: Dict[str, Any]) -> str:
        """Шифрует данные"""
        json_data = json.dumps(data).encode()
        encrypted_data = self.cipher.encrypt(json_data)
        return encrypted_data.decode()
    
    def decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Расшифровывает данные"""
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data.encode())
            return json.loads(decrypted_data.decode())
        except Exception:
            return {}
