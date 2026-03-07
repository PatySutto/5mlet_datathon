"""Configuração centralizada da aplicação."""

from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # App info
    APP_NAME: str = "Pedras Classification API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Upload settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".xlsx", ".xls"]
    ALLOWED_CONTENT_TYPES: List[str] = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "application/vnd.ms-excel"  # .xls
    ]
    UPLOAD_DIR: Path = Path("uploads")
    
    # Directories
    BASE_DIR: Path = Path(__file__).parent.parent
    MODEL_DIR: Path = BASE_DIR / "app" / "modelo"
    TREATED_DATA_DIR: Path = BASE_DIR / "src" / "bases" / "treated"
    FEATURES_DIR: Path = BASE_DIR / "src" / "bases" / "features"
    SRC_DIR: Path = BASE_DIR / "src"
    
    # Training default parameters
    DEFAULT_MAX_DEPTH: int = 6
    DEFAULT_N_ESTIMATORS: int = 100
    DEFAULT_LEARNING_RATE: float = 0.1
    DEFAULT_TEST_SIZE: float = 0.2
    DEFAULT_RANDOM_STATE: int = 42
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Required columns for data
    REQUIRED_COLUMNS: List[str] = ['PEDRA', 'IPV', 'IPS', 'IAN', 'IEG', 'INDE', 'IAA', 'IDA']
    FEATURE_COLUMNS: List[str] = ['IPV', 'IPS', 'IAN', 'IEG', 'INDE', 'IAA', 'IDA']
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instância global de configurações
settings = Settings()


# Criar diretórios necessários
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
settings.TREATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.FEATURES_DIR.mkdir(parents=True, exist_ok=True)
