import httpx
from typing import Dict
from app.config import config

class BitrixHandler:
    def __init__(self):
        self.webhook_url = config.BITRIX_WEBHOOK_URL
    
    async def send_message(self, dialog_id: str, message: str):
        """Отправка сообщения в чат Битрикс24"""
        url = f"{self.webhook_url}imbot.message.add"
        
        payload = {
            "DIALOG_ID": dialog_id,
            "MESSAGE": message
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"❌ Ошибка отправки сообщения: {e}")
                return None
    
    async def register_bot(self):
        """Регистрация бота в Битрикс24"""
        url = f"{self.webhook_url}imbot.register"
        
        payload = {
            "CODE": config.BITRIX_BOT_CODE,
            "TYPE": "B",  # Bot
            "EVENT_MESSAGE_ADD": f"{self.get_app_url()}/webhook/message",
            "PROPERTIES": {
                "NAME": "AI Knowledge Assistant",
                "COLOR": "PURPLE",
                "EMAIL": "ai-bot@company.com",
                "PERSONAL_BIRTHDAY": "2025-01-01",
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
    
    def get_app_url(self):
        """Получить URL приложения (замените на ваш реальный URL)"""
        return "https://ваше-приложение.railway.app"  # Измените после деплоя
