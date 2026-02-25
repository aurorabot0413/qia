"""
Configuración de QiA
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Google Cloud
    PROJECT_ID: str = "core-trees-487719-n8"
    REGION: str = "us-central1"
    
    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    
    # Vertex AI
    VERTEX_AI_LOCATION: str = "us-central1"
    GEMINI_MODEL: str = "gemini-2.5-pro"
    
    # Cloud Build
    CLOUD_BUILD_TRIGGER_NAME: str = "qia-qa-pipeline"
    
    # Storage
    BUCKET_NAME: str = "qia-artifacts-bucket"
    
    # App
    APP_NAME: str = "QiA"
    APP_VERSION: str = "0.1.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
