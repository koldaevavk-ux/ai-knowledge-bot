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
    print("🚀 AI Knowledge Bot запущен")

@app.get("/")
async def root():
    return {"status": "AI Knowledge Bot is running", "version": "1.1"}

@app.post("/webhook/message")
async def handle_message(request: Request, background_tasks: BackgroundTasks):
    """Обработка входящих сообщений от Битрикс24"""
    try:
        # Битрикс присылает данные как form-data, а не JSON
        form_data = await request.form()
        data = dict(form_data)
        
        event = data.get("event")
        
        if event == "ONIMBOTMESSAGEADD":
            # Битрикс присылает параметры в плоском формате data[PARAMS][...]
            user_message = data.get("data[PARAMS][MESSAGE]", "")
            dialog_id = data.get("data[PARAMS][DIALOG_ID]", "")
            from_user_id = data.get("data[PARAMS][FROM_USER_ID]", "")
            bot_id = data.get("data[PARAMS][BOT_ID]", "")
            
            # Игнорируем сообщения от самого себя (бота)
            if from_user_id and bot_id and str(from_user_id) == str(bot_id):
                return JSONResponse({"status": "ignored - bot message"})
            
            if not user_message or not dialog_id:
                print(f"⚠️ Получены неполные данные: message={user_message}, dialog={dialog_id}")
                return JSONResponse({"status": "missing data"})
            
            print(f"📨 Сообщение от пользователя: {user_message}")
            
            # Обрабатываем вопрос в фоне, чтобы Битрикс не ждал
            background_tasks.add_task(
                process_question,
                dialog_id,
                user_message
            )
            
            return JSONResponse({"status": "processing started"})
        
        return JSONResponse({"status": f"event {event} received but not handled"})
    
    except Exception as e:
        print(f"❌ Ошибка обработки webhook: {e}")
        # Логируем тело для отладки
        try:
            body = await request.body()
            print(f"DEBUG: Тело запроса: {body.decode()}")
        except:
            pass
        return JSONResponse({"status": "error", "message": str(e)})

async def process_question(dialog_id: str, question: str):
    """Обработка вопроса и отправка ответа"""
    try:
        # 1. Сразу сообщаем пользователю, что начали работу
        await bitrix_handler.send_message(dialog_id, "⏳ Ищу информацию в базе знаний...")
        
        # 2. Получаем ответ от AI
        answer = ai_engine.answer_question(question)
        
        # 3. Отправляем финальный ответ
        await bitrix_handler.send_message(dialog_id, answer)
        
    except Exception as e:
        print(f"❌ Ошибка в process_question: {e}")
        error_msg = f"❌ Извините, произошла ошибка: {str(e)}"
        await bitrix_handler.send_message(dialog_id, error_msg)
