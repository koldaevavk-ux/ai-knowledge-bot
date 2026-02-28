import httpx
from typing import Dict
from app.config import config

class BitrixHandler:
    def __init__(self):
        # Удаляем лишний слеш в конце, если он есть
        self.webhook_url = config.BITRIX_WEBHOOK_URL.rstrip('/')
    
    async def send_message(self, dialog_id: str, message: str):
        """Отправка сообщения в чат Битрикс24"""
        url = f"{self.webhook_url}/imbot.message.add"
        
        payload = {
            "DIALOG_ID": dialog_id,
            "MESSAGE": message
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                result = response.json()
                if "error" in result:
                    print(f"❌ Ошибка Битрикс при отправке: {result['error']} - {result.get('error_description')}")
                return result
            except Exception as e:
                print(f"❌ Ошибка отправки сообщения: {e}")
                return None
    
    async def register_bot(self):
        """Регистрация бота в Битрикс24 через метод imbot.register"""
        url = f"{self.webhook_url}/imbot.register"
        
        # Используем APP_URL из конфига
        app_url = config.APP_URL.rstrip('/')
        
        payload = {
            "CODE": config.BITRIX_BOT_CODE,
            "TYPE": "B",
            "EVENT_MESSAGE_ADD": f"{app_url}/webhook/message",
            "PROPERTIES": {
                "NAME": "AI Knowledge Assistant",
                "COLOR": "PURPLE",
                "WORK_POSITION": "AI Помощник по базе знаний"
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                result = response.json()
                print(f"✅ Бот зарегистрирован: {result}")
                return result
            except Exception as e:
                print(f"❌ Ошибка регистрации бота: {e}")
                return None
