"""Schemas Pydantic para validação de requisições e respostas."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Status de uma task de treinamento."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TrainingStage(str, Enum):
    """Estágio do pipeline de treinamento."""
    UPLOAD = "upload"
    PREPROCESSING = "preprocessing"
    FEATURE_ENGINEERING = "feature_engineering"
    TRAINING = "training"
    EVALUATION = "evaluation"
    SAVING = "saving"
    COMPLETED = "completed"


class TrainingParameters(BaseModel):
    """Parâmetros opcionais para treinamento do modelo."""
    max_depth: Optional[int] = Field(6, ge=3, le=10, description="Profundidade máxima das árvores")
    n_estimators: Optional[int] = Field(100, ge=50, le=500, description="Número de árvores")
    learning_rate: Optional[float] = Field(0.1, ge=0.01, le=0.3, description="Taxa de aprendizado")
    test_size: Optional[float] = Field(0.2, ge=0.1, le=0.3, description="Proporção do test set")
    random_state: Optional[int] = Field(42, description="Seed para reprodutibilidade")
    use_feast: Optional[bool] = Field(True, description="Usar Feast feature store")
    
    class Config:
        json_schema_extra = {
            "example": {
                "max_depth": 6,
                "n_estimators": 100,
                "learning_rate": 0.1,
                "test_size": 0.2,
                "random_state": 42,
                "use_feast": True
            }
        }


class ValidationInfo(BaseModel):
    """Informações de validação do arquivo."""
    valid_records: int = Field(..., description="Número de registros válidos")
    rejected_records: int = Field(..., description="Número de registros rejeitados")
    warnings: List[str] = Field(default_factory=list, description="Avisos durante validação")
    total_records: int = Field(..., description="Total de registros no arquivo")


class UploadResponse(BaseModel):
    """Resposta do upload de arquivo."""
    status: str = Field(..., description="Status da operação")
    message: str = Field(..., description="Mensagem descritiva")
    file_id: str = Field(..., description="ID único do arquivo")
    filename: str = Field(..., description="Nome do arquivo original")
    validation: ValidationInfo = Field(..., description="Informações de validação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Arquivo validado e preprocessado com sucesso",
                "file_id": "abc123",
                "filename": "dados.xlsx",
                "validation": {
                    "valid_records": 45,
                    "rejected_records": 3,
                    "warnings": ["3 linhas rejeitadas por ter menos de 2 features válidas"],
                    "total_records": 48
                }
            }
        }


class TrainingStatus(BaseModel):
    """Status de uma tarefa de treinamento."""
    task_id: str = Field(..., description="ID da tarefa")
    status: TaskStatus = Field(..., description="Status atual")
    progress: int = Field(..., ge=0, le=100, description="Progresso em percentual")
    stage: TrainingStage = Field(..., description="Estágio atual do pipeline")
    message: str = Field(..., description="Mensagem descritiva")
    started_at: Optional[datetime] = Field(None, description="Timestamp de início")
    completed_at: Optional[datetime] = Field(None, description="Timestamp de conclusão")
    error: Optional[str] = Field(None, description="Mensagem de erro se falhou")
    result: Optional['TrainingResult'] = Field(None, description="Resultado completo do treinamento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-123",
                "status": "running",
                "progress": 65,
                "stage": "training",
                "message": "Treinando modelo com 45 registros...",
                "started_at": "2026-03-07T10:30:00Z",
                "completed_at": None,
                "error": None
            }
        }


class ClassMetrics(BaseModel):
    """Métricas para uma classe específica."""
    precision: float = Field(..., description="Precisão")
    recall: float = Field(..., description="Recall")
    f1_score: float = Field(..., description="F1-Score")
    support: int = Field(..., description="Número de amostras")


class TrainingMetrics(BaseModel):
    """Métricas gerais do treinamento."""
    accuracy: float = Field(..., description="Acurácia geral")
    precision_macro: float = Field(..., description="Precisão macro")
    recall_macro: float = Field(..., description="Recall macro")
    f1_macro: float = Field(..., description="F1-Score macro")
    precision_weighted: float = Field(..., description="Precisão ponderada")
    recall_weighted: float = Field(..., description="Recall ponderada")
    f1_weighted: float = Field(..., description="F1-Score ponderada")


class ModelFiles(BaseModel):
    """Arquivos do modelo salvos."""
    model: str = Field(..., description="Nome do arquivo do modelo")
    encoder: str = Field(..., description="Nome do arquivo do encoder")
    features: str = Field(..., description="Nome do arquivo de features")


class TrainingResult(BaseModel):
    """Resultado completo do treinamento."""
    task_id: str = Field(..., description="ID da tarefa")
    status: TaskStatus = Field(..., description="Status final")
    model_id: str = Field(..., description="ID/data do modelo") 
    metrics: TrainingMetrics = Field(..., description="Métricas gerais")
    per_class_metrics: Dict[str, ClassMetrics] = Field(..., description="Métricas por classe")
    feature_importance: Dict[str, float] = Field(..., description="Importância das features")
    model_files: ModelFiles = Field(..., description="Arquivos salvos")
    parameters: TrainingParameters = Field(..., description="Parâmetros utilizados")
    completed_at: datetime = Field(..., description="Timestamp de conclusão")
    duration_seconds: float = Field(..., description="Duração em segundos")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-123",
                "status": "completed",
                "model_id": "2026-03-07",
                "metrics": {
                    "accuracy": 0.30,
                    "precision_macro": 0.17,
                    "recall_macro": 0.25,
                    "f1_macro": 0.19,
                    "precision_weighted": 0.23,
                    "recall_weighted": 0.30,
                    "f1_weighted": 0.25
                },
                "per_class_metrics": {
                    "Ametista": {"precision": 0.0, "recall": 0.0, "f1_score": 0.0, "support": 2}
                },
                "feature_importance": {
                    "IPV": 0.19, "IEG": 0.17, "IDA": 0.16
                },
                "model_files": {
                    "model": "xgboost_pedra_classifier_2026-03-07.joblib",
                    "encoder": "label_encoder_2026-03-07.pkl",
                    "features": "feature_names_2026-03-07.pkl"
                },
                "parameters": {
                    "max_depth": 6,
                    "n_estimators": 100,
                    "learning_rate": 0.1,
                    "test_size": 0.2,
                    "random_state": 42,
                    "use_feast": True
                },
                "completed_at": "2026-03-07T10:35:23Z",
                "duration_seconds": 45.2
            }
        }


class ErrorResponse(BaseModel):
    """Resposta de erro."""
    status: str = Field("error", description="Status da operação")
    error_code: str = Field(..., description="Código do erro")
    message: str = Field(..., description="Mensagem de erro")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error_code": "VALIDATION_ERROR",
                "message": "Arquivo de entrada inválido",
                "details": {
                    "missing_columns": ["PEDRA"],
                    "required_columns": ["PEDRA", "IPV", "IPS", "IAN", "IEG", "INDE", "IAA", "IDA"]
                }
            }
        }


class HealthResponse(BaseModel):
    """Resposta do health check."""
    status: str = Field(..., description="Status da aplicação")
    version: str = Field(..., description="Versão da aplicação")
    models_available: int = Field(..., description="Número de modelos disponíveis")


class ModelInfo(BaseModel):
    """Informações de um modelo."""
    model_id: str = Field(..., description="ID do modelo")
    files: ModelFiles = Field(..., description="Arquivos do modelo")
    created_at: str = Field(..., description="Data de criação")


# Resolver forward references
TrainingStatus.model_rebuild()
