"""Serviço de treinamento do modelo."""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Callable
from fastapi import HTTPException

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.train import (
    load_data_for_training,
    train_model,
    evaluate_model,
    save_model_artifacts,
    print_feature_importance
)
from app.models.schemas import (
    TrainingParameters,
    TrainingResult,
    TrainingMetrics,
    ClassMetrics,
    ModelFiles,
    TaskStatus
)
from app.services.feature_engineering_service import (
    prepare_features_for_training,
    skip_feature_engineering
)


async def train_model_pipeline(
    parameters: TrainingParameters,
    progress_callback: Callable[[int, str, str], None] = None
) -> TrainingResult:
    """
    Executa pipeline completo de treinamento.
    
    Args:
        parameters: Parâmetros de treinamento
        progress_callback: Função callback para reportar progresso (progress, stage, message)
        
    Returns:
        TrainingResult com métricas e informações do modelo
        
    Raises:
        HTTPException: Se houver erro no treinamento
    """
    start_time = datetime.now()
    
    try:
        # Stage 1: Feature Engineering (se habilitado)
        if progress_callback:
            progress_callback(10, "feature_engineering", "Preparando features...")
        
        if parameters.use_feast:
            feature_info = prepare_features_for_training()
        else:
            feature_info = skip_feature_engineering()
        
        # Stage 2: Carregar dados
        if progress_callback:
            progress_callback(30, "training", "Carregando dados de treinamento...")
        
        X, y = load_data_for_training()
        
        # Stage 3: Treinar modelo
        if progress_callback:
            progress_callback(40, "training", f"Treinando modelo com {len(X)} registros...")
        
        model, encoder, X_test, y_test, X_train, y_train = train_model(
            X, y,
            max_depth=parameters.max_depth,
            n_estimators=parameters.n_estimators,
            learning_rate=parameters.learning_rate,
            test_size=parameters.test_size,
            random_state=parameters.random_state,
            verbose=False  # Desabilitar prints durante API
        )
        
        # Stage 4: Avaliar modelo
        if progress_callback:
            progress_callback(70, "evaluation", "Avaliando performance do modelo...")
        
        metrics_dict = evaluate_model(model, encoder, X_test, y_test)
        
        # Extrair métricas gerais
        training_metrics = TrainingMetrics(
            accuracy=metrics_dict['accuracy'],
            precision_macro=metrics_dict['classification_report']['macro avg']['precision'],
            recall_macro=metrics_dict['classification_report']['macro avg']['recall'],
            f1_macro=metrics_dict['classification_report']['macro avg']['f1-score'],
            precision_weighted=metrics_dict['classification_report']['weighted avg']['precision'],
            recall_weighted=metrics_dict['classification_report']['weighted avg']['recall'],
            f1_weighted=metrics_dict['classification_report']['weighted avg']['f1-score']
        )
        
        # Extrair métricas por classe
        per_class_metrics = {}
        for class_name in encoder.classes_:
            class_data = metrics_dict['classification_report'].get(class_name, {})
            if class_data:
                per_class_metrics[class_name] = ClassMetrics(
                    precision=class_data.get('precision', 0.0),
                    recall=class_data.get('recall', 0.0),
                    f1_score=class_data.get('f1-score', 0.0),
                    support=int(class_data.get('support', 0))
                )
        
        # Extrair importância das features
        feature_importance = {}
        importances = model.feature_importances_
        for feature_name, importance in zip(X.columns, importances):
            feature_importance[feature_name] = float(importance)
        
        # Stage 5: Salvar modelo
        if progress_callback:
            progress_callback(90, "saving", "Salvando artefatos do modelo...")
        
        save_model_artifacts(
            model, 
            encoder, 
            X.columns.tolist(),
            save_enabled=True
        )
        
        # Construir nomes dos arquivos
        today = datetime.now().strftime('%Y-%m-%d')
        model_files = ModelFiles(
            model=f"xgboost_pedra_classifier_{today}.joblib",
            encoder=f"label_encoder_{today}.pkl",
            features=f"feature_names_{today}.pkl"
        )
        
        # Calcular duração
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Construir resultado
        result = TrainingResult(
            task_id="",  # Será preenchido pelo caller
            status=TaskStatus.COMPLETED,
            model_id=today,
            metrics=training_metrics,
            per_class_metrics=per_class_metrics,
            feature_importance=feature_importance,
            model_files=model_files,
            parameters=parameters,
            completed_at=end_time,
            duration_seconds=duration
        )
        
        if progress_callback:
            progress_callback(100, "completed", "Treinamento concluído com sucesso!")
        
        return result
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "DATA_NOT_FOUND",
                "message": f"Dados de treinamento não encontrados: {str(e)}",
                "details": {"exception": str(type(e).__name__)}
            }
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "TRAINING_ERROR",
                "message": f"Erro durante treinamento: {str(e)}",
                "details": {
                    "exception": str(type(e).__name__),
                    "traceback": error_details
                }
            }
        )
