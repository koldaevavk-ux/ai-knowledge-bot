import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from groq import Groq
from typing import List, Dict
from app.config import config
from app.document_loader import DocumentLoader

class AIEngine:
    def __init__(self):
        # Настройка Groq
        self.groq_client = Groq(api_key=config.GROQ_API_KEY)
        
        # Настройка Google для embeddings
        genai.configure(api_key=config.GOOGLE_API_KEY)
        
        # ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=config.CHROMA_PATH)
        self.collection_name = "knowledge_base"
        
        # Инициализация базы знаний
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Инициализация векторной базы знаний"""
        try:
            # Пробуем получить существующую коллекцию
            self.collection = self.chroma_client.get_collection(
                name=self.collection_name
            )
            print(f"✅ Коллекция '{self.collection_name}' загружена")
        except:
            # Создаем новую коллекцию
            print("📚 Создание новой базы знаний...")
            loader = DocumentLoader()
            documents = loader.load_all_documents()
            
            if not documents:
                print("⚠️ Документы не найдены в data/documents/")
                return
            
            # Создаем embeddings
            embeddings = []
            texts = []
            metadatas = []
            ids = []
            
            for i, doc in enumerate(documents):
                text = doc.page_content
                texts.append(text)
                metadatas.append(doc.metadata)
                ids.append(f"doc_{i}")
                
                # Создаем embedding через Google
                embedding = genai.embed_content(
                    model=config.EMBEDDING_MODEL,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(embedding['embedding'])
            
            # Создаем коллекцию
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Corporate knowledge base"}
            )
            
            # Добавляем документы
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ База знаний создана: {len(documents)} чанков")
    
    def get_embedding(self, text: str) -> List[float]:
        """Получение embedding для запроса"""
        result = genai.embed_content(
            model=config.EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
    
    def search_knowledge(self, query: str) -> List[Dict]:
        """Поиск релевантных документов"""
        query_embedding = self.get_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=config.TOP_K_RESULTS
        )
        
        documents = []
        for i in range(len(results['documents'][0])):
            documents.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return documents
    
    def generate_answer(self, question: str, context_docs: List[Dict]) -> str:
        """Генерация ответа с использованием Groq"""
        
        # Формируем контекст из найденных документов
        context = "\n\n---\n\n".join([
            f"Документ: {doc['metadata']['source']}\n{doc['content']}"
            for doc in context_docs
        ])
        
        # Промпт для LLM
        system_prompt = """Ты — корпоративный AI-ассистент, который отвечает на вопросы сотрудников на основе базы знаний компании.

Правила:
1. Отвечай ТОЛЬКО на основе предоставленного контекста
2. Если информации нет в контексте — честно скажи "В базе знаний нет информации по этому вопросу"
3. Всегда указывай источник (название документа)
4. Отвечай на русском языке
5. Будь кратким и точным

Формат ответа:
[Ответ на вопрос]

📄 Источник: [название документа]"""

        user_prompt = f"""Контекст из базы знаний:
{context}

Вопрос сотрудника: {question}

Пожалуйста, ответь на вопрос."""

        try:
            response = self.groq_client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"❌ Ошибка при генерации ответа: {str(e)}"
    
    def answer_question(self, question: str) -> str:
        """Основной метод: поиск + генерация ответа"""
        # Поиск релевантных документов
        relevant_docs = self.search_knowledge(question)
        
        if not relevant_docs:
            return "К сожалению, я не нашел релевантной информации в базе знаний по вашему вопросу."
        
        # Генерация ответа
        answer = self.generate_answer(question, relevant_docs)
        
        return answer
