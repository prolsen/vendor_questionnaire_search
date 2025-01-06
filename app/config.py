# app/config.py
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    QDRANT_SERVER: Optional[str] = "localhost"
    QDRANT_PORT: Optional[int] = 6333
    QDRANT_VECTOR_COLLECTION: Optional[str] = "questions_and_answers_rag_vector"
    QDRANT_STORAGE_PATH: Optional[str] = "/app/storage/qdrant"
    
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_LLM_MODEL: Optional[str] = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: Optional[str] = "text-embedding-3-large"
    
    TEMPERATURE: float = 0.2
    
    COHERE_API_KEY: Optional[str] = None
    
    COMPANY_NAME: Optional[str] = "ACME Corp"
    
    # Storage paths
    QA_DIRECTORY_PATH: Optional[str] = "/app/data/questions_and_answers"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }

settings = Settings()