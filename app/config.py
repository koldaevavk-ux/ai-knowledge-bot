import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Битрикс24
    BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
    BITRIX_BOT_CODE = os.getenv("BITRIX_BOT_CODE", "knowledge_assistant")
    
    # URL приложения для регистрации вебхуков (берется из окружения или ставится заглушка)
    APP_URL = os.getenv("APP_URL", "https://ai-knowledge-bot-577762118407.us-east1.run.app")
    
    # AI
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # RAG Settings
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", 3))
    
    # Paths
    DOCUMENTS_PATH = "data/documents"
    CHROMA_PATH = "chroma_db"
    
    # Models
    EMBEDDING_MODEL = "models/gemini-embedding-001"
    LLM_MODEL = "llama-3.3-70b-versatile"

config = Config()
