Get started by customizing your environment (defined in the .idx/dev.nix file) with the tools and IDE extensions you'll need for your project!

Learn more at https://developers.google.com/idx/guides/customize-idx-env

ai-knowledge-bot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение
│   ├── bitrix_handler.py    # Обработка Битрикс24
│   ├── ai_engine.py         # AI логика (RAG)
│   ├── document_loader.py   # Загрузка PDF/DOC
│   └── config.py            # Конфигурация
├── data/
│   └── documents/           # Ваши PDF/DOC файлы
├── chroma_db/               # Векторная база (создастся автоматически)
├── requirements.txt
├── .env
└── README.md