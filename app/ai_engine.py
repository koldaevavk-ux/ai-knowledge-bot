import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from groq import Groq
from typing import List, Dict
import os
from app.config import config
from app.document_loader import DocumentLoader

class AIEngine:
    def __init__(self):
        # Настройка Groq
        self.groq_client = Groq(api_key=config.GROQ_API_KEY)
        
        # Настройка Google для embeddings
        genai.configure(api_key=config.GOOGLE_API_KEY)
        
        # ChromaDB - используем PersistentClient
        self.chroma_client = chromadb.PersistentClient(path=config.CHROMA_PATH)
        self.collection_name = "knowledge_base"
        self.collection = None
        
        # Инициализация базы знаний
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Инициализация векторной базы знаний"""
        try:
            # Используем get_or_create_collection, чтобы не падать
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Corporate knowledge base"}
            )
            
            count = self.collection.count()
            if count > 0:
                print(f"✅ Коллекция '{self.collection_name}' загружена ({count} чанков)")
                return

            print("📚 База пуста. Начинаю автоматическую индексацию...")
            loader = DocumentLoader()
            documents = loader.load_all_documents()
            
            if not documents:
                print("⚠️ Документы не найдены в data/documents/")
                return
            
            embeddings = []
            texts = []
            metadatas = []
            ids = []
            
            for i, doc in enumerate(documents):
                try:
                    embedding = genai.embed_content(
                        model=config.EMBEDDING_MODEL,
                        content=doc.page_content,
                        task_type="retrieval_document"
                    )
                    embeddings.append(embedding['embedding'])
                    texts.append(doc.page_content)
                    metadatas.append(doc.metadata)
                    ids.append(f"doc_{i}")
                except Exception as e:
                    print(f"❌ Ошибка эмбеддинга для чанка {i}: {e}")
                    continue
            
            if embeddings:
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"✅ Индексация завершена: {self.collection.count()} чанков добавлено")
            
        except Exception as e:
            print(f"🚨 Ошибка инициализации AI Engine: {e}")

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
        if not self.collection or self.collection.count() == 0:
            print("⚠️ Поиск невозможен: коллекция пуста или не инициализирована")
            return []

        try:
            query_embedding = self.get_embedding(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=config.TOP_K_RESULTS
            )
            
            documents = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    documents.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i]
                    })
            return documents
        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")
            return []
    
    def generate_answer(self, question: str, context_docs: List[Dict]) -> str:
        """Генерация ответа через Groq"""
        if not context_docs:
            return "В базе знаний нет информации по этому вопросу."

        context = "\n\n---\n\n".join([
            f"Документ: {doc['metadata'].get('source', 'Неизвестен')}\n{doc['content']}"
            for doc in context_docs
        ])
        
        system_prompt = """Ты — корпоративный ассистент. Отвечай ТОЛЬКО по контексту. 
Указывай источник. Будь краток."""

        user_prompt = f"Контекст:\n{context}\n\nВопрос: {question}"

        try:
            response = self.groq_client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Ошибка генерации: {str(e)}"
    
    def answer_question(self, question: str) -> str:
        relevant_docs = self.search_knowledge(question)
        return self.generate_answer(question, relevant_docs)
