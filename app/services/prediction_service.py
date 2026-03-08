"""Serviço de predição usando modelos treinados."""

import sys
import uuid
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime
import pandas as pd
import numpy as np
import joblib
from fastapi import HTTPException

# Adicionar src ao path para imports (se necessário)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from app.models.schemas import PredictionInput, PredictionResult
from app.config import settings

# Features esperadas
REQUIRED_FEATURES = ['IPV', 'IPS', 'IAN', 'IEG', 'INDE', 'IAA', 'IDA']


def load_model_artifacts(model_id: Optional[str] = None) -> Tuple:
    """
    Carrega artefatos do modelo (model, encoder, features).
    
    Args:
        model_id: ID específico do modelo (formato: YYYY-MM-DD). 
                  Se None, usa o mais recente.
    
    Returns:
        Tupla (model, label_encoder, feature_names, model_id_used)
        
    Raises:
        HTTPException: Se modelo não for encontrado
    """
    models_dir = settings.MODEL_DIR
    
    if not models_dir.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "MODEL_DIR_NOT_FOUND",
                "message": f"Diretório de modelos não encontrado: {models_dir}"
            }
        )
    
    # Buscar arquivos do modelo
    if model_id:
        # Modelo específico
        model_file = models_dir / f"xgboost_pedra_classifier_{model_id}.joblib"
        encoder_file = models_dir / f"label_encoder_{model_id}.pkl"
        feature_file = models_dir / f"feature_names_{model_id}.pkl"
        
        if not model_file.exists():
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "MODEL_NOT_FOUND",
                    "message": f"Modelo com ID '{model_id}' não encontrado",
                    "available_models": _list_available_model_ids()
                }
            )
    else:
        # Modelo mais recente
        model_files = list(models_dir.glob('xgboost_pedra_classifier_*.joblib'))
        
        if not model_files:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "NO_MODELS_AVAILABLE",
                    "message": "Nenhum modelo treinado disponível",
                    "hint": "Treine um modelo primeiro na aba 'Treinamento'"
                }
            )
        
        # Ordenar por data de modificação e pegar o mais recente
        model_file = max(model_files, key=lambda x: x.stat().st_mtime)
        
        # Extrair model_id do nome do arquivo
        model_id = model_file.stem.replace('xgboost_pedra_classifier_', '')
        
        encoder_file = models_dir / f"label_encoder_{model_id}.pkl"
        feature_file = models_dir / f"feature_names_{model_id}.pkl"
    
    # Verificar se todos os arquivos existem
    missing_files = []
    if not model_file.exists():
        missing_files.append(model_file.name)
    if not encoder_file.exists():
        missing_files.append(encoder_file.name)
    if not feature_file.exists():
        missing_files.append(feature_file.name)
    
    if missing_files:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INCOMPLETE_MODEL",
                "message": f"Modelo incompleto (arquivos faltando): {', '.join(missing_files)}"
            }
        )
    
    # Carregar artefatos
    try:
        model = joblib.load(model_file)
        label_encoder = joblib.load(encoder_file)
        feature_names = joblib.load(feature_file)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "MODEL_LOAD_ERROR",
                "message": f"Erro ao carregar modelo: {str(e)}"
            }
        )
    
    return model, label_encoder, feature_names, model_id


def _list_available_model_ids() -> list:
    """Lista IDs dos modelos disponíveis."""
    models_dir = settings.MODEL_DIR
    model_files = list(models_dir.glob('xgboost_pedra_classifier_*.joblib'))
    
    model_ids = []
    for file in model_files:
        model_id = file.stem.replace('xgboost_pedra_classifier_', '')
        model_ids.append(model_id)
    
    return sorted(model_ids, reverse=True)


def predict_single(prediction_input: PredictionInput) -> PredictionResult:
    """
    Realiza predição para um único input.
    
    Args:
        prediction_input: Input com as 7 features e model_id opcional
        
    Returns:
        PredictionResult com pedra predita, confiança e probabilidades
        
    Raises:
        HTTPException: Em caso de erro na predição
    """
    # Carregar modelo
    model, label_encoder, feature_names, model_id_used = load_model_artifacts(
        prediction_input.model_id
    )
    
    # Criar DataFrame com as features
    features_dict = {
        'IPV': prediction_input.IPV,
        'IPS': prediction_input.IPS,
        'IAN': prediction_input.IAN,
        'IEG': prediction_input.IEG,
        'INDE': prediction_input.INDE,
        'IAA': prediction_input.IAA,
        'IDA': prediction_input.IDA
    }
    
    df = pd.DataFrame([features_dict])
    
    # Garantir ordem correta das features
    X = df[REQUIRED_FEATURES].values
    
    try:
        # Fazer predição
        y_pred_encoded = model.predict(X)
        y_pred_proba = model.predict_proba(X)
        
        # Decodificar classe
        y_pred = label_encoder.inverse_transform(y_pred_encoded)
        pedra_predita = y_pred[0]
        
        # Extrair probabilidades
        probabilidades = {}
        for i, class_name in enumerate(label_encoder.classes_):
            probabilidades[class_name] = float(y_pred_proba[0, i])
        
        # Confiança = probabilidade máxima
        confianca = float(y_pred_proba[0].max())
        
        return PredictionResult(
            pedra_predita=pedra_predita,
            confianca=confianca,
            probabilidades=probabilidades,
            model_used=model_id_used
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "PREDICTION_ERROR",
                "message": f"Erro ao realizar predição: {str(e)}"
            }
        )


def predict_batch_from_file(file_path: Path, model_id: Optional[str] = None) -> Tuple[Path, Dict]:
    """
    Realiza predições em batch a partir de arquivo Excel.
    
    Args:
        file_path: Caminho do arquivo Excel de entrada
        model_id: ID do modelo (None = mais recente)
    
    Returns:
        Tupla (output_file_path, stats_dict)
    """
    # Carregar modelo
    model, label_encoder, feature_names, model_id_used = load_model_artifacts(model_id)
    
    # Ler Excel
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "FILE_READ_ERROR",
                "message": f"Erro ao ler arquivo Excel: {str(e)}"
            }
        )
    
    # Validar que possui as features necessárias
    missing_columns = [col for col in REQUIRED_FEATURES if col not in df.columns]
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MISSING_COLUMNS",
                "message": f"Colunas faltando no arquivo: {', '.join(missing_columns)}",
                "required_columns": REQUIRED_FEATURES
            }
        )
    
    # Copiar DF original para preservar todas as colunas
    df_result = df.copy()
    
    # Extrair apenas as features para predição
    df_features = df[REQUIRED_FEATURES].copy()
    
    # Converter para numérico e preencher NaN com 0
    for col in REQUIRED_FEATURES:
        df_features[col] = pd.to_numeric(df_features[col], errors='coerce').fillna(0)
    
    warnings = []
    successful = 0
    failed = 0
    
    # Fazer predições
    try:
        X = df_features[REQUIRED_FEATURES].values
        y_pred_encoded = model.predict(X)
        y_pred_proba = model.predict_proba(X)
        y_pred = label_encoder.inverse_transform(y_pred_encoded)
        
        # Adicionar coluna PEDRA ao resultado
        df_result['PEDRA'] = y_pred
        
        # Adicionar confiança (opcional)
        df_result['CONFIANCA'] = y_pred_proba.max(axis=1)
        
        successful = len(df_result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "PREDICTION_ERROR",
                "message": f"Erro durante predição: {str(e)}"
            }
        )
    
    # Salvar resultado
    output_dir = Path(__file__).parent.parent.parent / "temp" / "predictions"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"predicao_batch_{timestamp}_{uuid.uuid4().hex[:8]}.xlsx"
    output_path = output_dir / output_filename
    
    try:
        df_result.to_excel(output_path, index=False)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "FILE_WRITE_ERROR",
                "message": f"Erro ao salvar arquivo de resultado: {str(e)}"
            }
        )
    
    stats = {
        "total_records": len(df),
        "successful": successful,
        "failed": failed,
        "warnings": warnings,
        "model_used": model_id_used,
        "output_file": output_filename
    }
    
    return output_path, stats

