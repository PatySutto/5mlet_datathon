"""Serviço de feature engineering com Feast."""

import sys
from pathlib import Path
from fastapi import HTTPException

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.feature_engineering import (
    prepare_feature_data,
    initialize_feature_store
)


def prepare_features_for_training() -> dict:
    """
    Prepara features usando Feast feature store.
    
    Returns:
        Dict com informações do processamento
        
    Raises:
        HTTPException: Se houver erro no feature engineering
    """
    try:
        # Prepara dados das features
        df = prepare_feature_data()
        
        # Inicializa feature store
        store = initialize_feature_store()
        
        return {
            "status": "success",
            "records_processed": len(df),
            "features": df.columns.tolist(),
            "message": "Features preparadas com sucesso no Feast"
        }
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "DATA_NOT_FOUND",
                "message": f"Arquivo tratado não encontrado: {str(e)}",
                "details": {"exception": str(type(e).__name__)}
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "FEATURE_ENGINEERING_ERROR",
                "message": f"Erro no feature engineering: {str(e)}",
                "details": {"exception": str(type(e).__name__)}
            }
        )


def skip_feature_engineering() -> dict:
    """
    Pula o feature engineering (modo simplificado).
    
    Returns:
        Dict indicando que foi pulado
    """
    return {
        "status": "skipped",
        "message": "Feature engineering pulado (modo simplificado)"
    }
