"""Rotas para health check e informações do sistema."""

from fastapi import APIRouter
from pathlib import Path
from typing import List

from app.models.schemas import HealthResponse, ModelInfo, ModelFiles
from app.config import settings


router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check da aplicação.
    
    Retorna status da aplicação e número de modelos disponíveis.
    """
    # Contar modelos disponíveis
    model_files = list(settings.MODEL_DIR.glob("xgboost_pedra_classifier_*.joblib"))
    
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        models_available=len(model_files)
    )


@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """
    Lista todos os modelos treinados disponíveis.
    
    Retorna informações sobre cada modelo incluindo data de criação.
    """
    models = []
    
    # Buscar todos os modelos
    model_files = sorted(
        settings.MODEL_DIR.glob("xgboost_pedra_classifier_*.joblib"),
        key=lambda x: x.stat().st_mtime,
        reverse=True  # Mais recente primeiro
    )
    
    for model_file in model_files:
        # Extrair timestamp do nome do arquivo
        # Formato antigo: xgboost_pedra_classifier_YYYY-MM-DD.joblib
        # Formato novo: xgboost_pedra_classifier_YYYY-MM-DD_HH-MM-SS.joblib
        model_name = model_file.stem  # Remove .joblib
        
        # Extrair timestamp: tudo após 'xgboost_pedra_classifier_'
        prefix = 'xgboost_pedra_classifier_'
        if model_name.startswith(prefix):
            model_id = model_name[len(prefix):]  # Pega tudo após o prefixo
            
            # Construir info dos arquivos relacionados
            encoder_file = f"label_encoder_{model_id}.pkl"
            features_file = f"feature_names_{model_id}.pkl"
            
            # Verificar se arquivos existem
            encoder_exists = (settings.MODEL_DIR / encoder_file).exists()
            features_exists = (settings.MODEL_DIR / features_file).exists()
            
            if encoder_exists and features_exists:
                models.append(
                    ModelInfo(
                        model_id=model_id,
                        files=ModelFiles(
                            model=model_file.name,
                            encoder=encoder_file,
                            features=features_file
                        ),
                        created_at=model_id  # O timestamp completo
                    )
                )
    
    return models


@router.get("/info")
async def app_info():
    """
    Informações detalhadas da aplicação.
    
    Retorna configurações e estatísticas gerais.
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "config": {
            "max_upload_size_mb": settings.MAX_UPLOAD_SIZE / (1024 * 1024),
            "allowed_extensions": settings.ALLOWED_EXTENSIONS,
            "required_columns": settings.REQUIRED_COLUMNS,
            "feature_columns": settings.FEATURE_COLUMNS
        },
        "training": {
            "default_max_depth": settings.DEFAULT_MAX_DEPTH,
            "default_n_estimators": settings.DEFAULT_N_ESTIMATORS,
            "default_learning_rate": settings.DEFAULT_LEARNING_RATE,
            "default_test_size": settings.DEFAULT_TEST_SIZE,
            "default_random_state": settings.DEFAULT_RANDOM_STATE
        }
    }
