"""Router para endpoints de predição."""

from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
from app.models.schemas import PredictionInput, PredictionResult, BatchPredictionResponse
from app.services.prediction_service import predict_single, predict_batch_from_file

router = APIRouter(prefix="/api/prediction", tags=["prediction"])


@router.post("", response_model=PredictionResult)
async def predict(input_data: PredictionInput) -> PredictionResult:
    """
    Realiza predição de classe de pedra baseada nas 7 features.
    
    Args:
        input_data: Features IPV, IPS, IAN, IEG, INDE, IAA, IDA e model_id opcional
        
    Returns:
        PredictionResult com pedra predita, confiança e probabilidades por classe
        
    Raises:
        HTTPException 404: Modelo não encontrado
        HTTPException 500: Erro durante predição
    """
    try:
        result = predict_single(input_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "PREDICTION_FAILED",
                "message": f"Falha na predição: {str(e)}"
            }
        )


@router.post("/batch", response_model=BatchPredictionResponse)
async def predict_batch(
    file: UploadFile = File(..., description="Arquivo Excel com features"),
    model_id: str = None
):
    """
    Realiza predição em batch a partir de arquivo Excel.
    
    Arquivo deve conter colunas: IPV, IPS, IAN, IEG, INDE, IAA, IDA
    Retorna arquivo Excel com coluna PEDRA adicionada.
    
    Args:
        file: Arquivo Excel (.xlsx ou .xls)
        model_id: ID do modelo (opcional, padrão: mais recente)
    
    Returns:
        BatchPredictionResponse com URL para download do resultado
    """
    # Validar extensão
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "INVALID_FILE_TYPE",
                "message": "Arquivo deve ser Excel (.xlsx ou .xls)"
            }
        )
    
    # Salvar arquivo temporário
    temp_dir = Path(__file__).parent.parent.parent / "temp" / "uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    temp_file_path = temp_dir / f"upload_{file.filename}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "FILE_SAVE_ERROR",
                "message": f"Erro ao salvar arquivo: {str(e)}"
            }
        )
    
    try:
        # Processar predição em batch
        output_path, stats = predict_batch_from_file(temp_file_path, model_id)
        
        # Construir resposta
        download_url = f"/api/prediction/download/{output_path.name}"
        
        return BatchPredictionResponse(
            status="success",
            message=f"Predições concluídas: {stats['successful']} registros processados",
            total_records=stats['total_records'],
            successful_predictions=stats['successful'],
            failed_predictions=stats['failed'],
            model_used=stats['model_used'],
            download_url=download_url,
            warnings=stats['warnings']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "BATCH_PREDICTION_FAILED",
                "message": f"Erro durante predição em batch: {str(e)}"
            }
        )
    finally:
        # Limpar arquivo temporário
        if temp_file_path.exists():
            temp_file_path.unlink()


@router.get("/download/{filename}")
async def download_prediction_result(filename: str):
    """
    Faz download do arquivo de resultado da predição em batch.
    
    Args:
        filename: Nome do arquivo gerado
    
    Returns:
        FileResponse com o arquivo Excel
    """
    output_dir = Path(__file__).parent.parent.parent / "temp" / "predictions"
    file_path = output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "FILE_NOT_FOUND",
                "message": "Arquivo de resultado não encontrado"
            }
        )
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

