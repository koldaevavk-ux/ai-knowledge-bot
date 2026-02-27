from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from app.bitrix_handler import BitrixHandler
from app.ai_engine import AIEngine
from app.config import config

app = FastAPI(title="AI Knowledge Bot for Bitrix24")

# Инициализация компонентов
ai_engine = AIEngine()
bitrix_handler = BitrixHandler()

@app.on_event("startup")
async def startup_event():
    """Запуск приложения"""
    print("🚀 AI Knowledge Bot запущен")
    # При первом запуске раскомментируйте для регистрации бота:
    # await bitrix_handler.register_bot()

@app.get("/")
async def root():
    return {"status": "AI Knowledge Bot is running", "version": "1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/webhook/message")
async def handle_message(request: Request, background_tasks: BackgroundTasks):
    """Обработка входящих сообщений от Битрикс24"""
    try:
        data = await request.json()
        print(f"📨 Получено сообщение: {data}")
        
        # Извлекаем данные
        event = data.get("event")
        
        if event == "ONIMBOTMESSAGEADD":
            message_data = data.get("data", {}).get("PARAMS", {})
            
            # Проверяем, что это не сообщение от бота
            if message_data.get("FROM_USER_ID") == message_data.get("BOT_ID"):
                return JSONResponse({"status": "ignored - bot message"})
            
            user_message = message_data.get("MESSAGE", "")
            dialog_id = message_data.get("DIALOG_ID", "")
            
            if not user_message or not dialog_id:
                return JSONResponse({"status": "no message or dialog"})
            
            # Обрабатываем вопрос в фоне
            background_tasks.add_task(
                process_question,
                dialog_id,
                user_message
            )
            
            return JSONResponse({"status": "processing"})
        
        return JSONResponse({"status": "ok"})
    
    except Exception as e:
        print(f"❌ Ошибка обработки webhook: {e}")
        return JSONResponse({"status": "error", "message": str(e)})

async def process_question(dialog_id: str, question: str):
    """Обработка вопроса и отправка ответа"""
    try:
        # Отправляем "печатает..."
        await bitrix_handler.send_message(dialog_id, "⏳ Ищу информацию в базе знаний...")
        
        # Получаем ответ от AI
        answer = ai_engine.answer_question(question)
        
        # Отправляем ответ
        await bitrix_handler.send_message(dialog_id, answer)
        
    except Exception as e:
        error_msg = f"❌ Извините, произошла ошибка при обработке вашего вопроса: {str(e)}"
        await bitrix_handler.send_message(dialog_id, error_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
