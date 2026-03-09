"""Rotas para operações de treinamento."""

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from app.models.schemas import (
    UploadResponse,
    TrainingParameters,
    TrainingStatus,
    TrainingResult,
    TaskStatus,
    TrainingStage
)
from app.services.file_service import (
    validate_upload_file,
    save_upload_file,
    cleanup_upload
)
from app.services.preprocessing_service import preprocess_uploaded_file
from app.services.training_service import train_model_pipeline
from app.utils.task_manager import task_manager


router = APIRouter(prefix="/api/training", tags=["Training"])


@router.post("/upload", response_model=UploadResponse)
async def upload_training_file(file: UploadFile = File(...)):
    """
    Upload e validação de arquivo para treinamento.
    
    Aceita arquivos Excel (.xlsx, .xls) com as colunas obrigatórias:
    PEDRA, IPV, IPS, IAN, IEG, INDE, IAA, IDA
    """
    # Validar arquivo
    await validate_upload_file(file)
    
    # Salvar arquivo
    file_id, file_path = await save_upload_file(file)
    
    try:
        # Preprocessar arquivo
        treated_file_path, validation_info = preprocess_uploaded_file(file_path)
        
        # Limpar arquivo temporário
        await cleanup_upload(file_path)
        
        # Construir resposta
        response = UploadResponse(
            status="success",
            message="Arquivo validado e preprocessado com sucesso",
            file_id=file_id,
            filename=file.filename,
            validation=validation_info
        )
        
        return response
        
    except HTTPException:
        # Limpar arquivo temporário em caso de erro
        await cleanup_upload(file_path)
        raise
    except Exception as e:
        # Limpar arquivo temporário  
        await cleanup_upload(file_path)
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "UPLOAD_ERROR",
                "message": f"Erro ao processar upload: {str(e)}"
            }
        )


@router.post("/start", response_model=dict)
async def start_training(
    background_tasks: BackgroundTasks,
    parameters: Optional[TrainingParameters] = None
):
    """
    Inicia treinamento do modelo em background.
    
    Parâmetros opcionais podem ser fornecidos para customizar o treinamento.
    Retorna um task_id para acompanhar o progresso.
    """
    # Usar parâmetros padrão se não fornecidos
    if parameters is None:
        parameters = TrainingParameters()
    
    # Criar task
    task_id = task_manager.create_task()
    
    # Adicionar tarefa ao background
    background_tasks.add_task(
        _train_model_background,
        task_id,
        parameters
    )
    
    return {
        "status": "started",
        "task_id": task_id,
        "message": "Treinamento iniciado em background",
        "parameters": parameters.model_dump()
    }


async def _train_model_background(task_id: str, parameters: TrainingParameters):
    """
    Função executada em background para treinar modelo.
    
    Args:
        task_id: ID da task
        parameters: Parâmetros de treinamento
    """
    def update_progress(progress: int, stage: str, message: str):
        """Callback para atualizar progresso."""
        task_manager.update_task(
            task_id=task_id,
            status=TaskStatus.RUNNING,
            progress=progress,
            stage=TrainingStage(stage),
            message=message
        )
    
    try:
        # Atualizar status inicial
        task_manager.update_task(
            task_id=task_id,
            status=TaskStatus.RUNNING,
            progress=5,
            stage=TrainingStage.PREPROCESSING,
            message="Iniciando pipeline de treinamento..."
        )
        
        # Executar pipeline de treinamento
        result = await train_model_pipeline(
            parameters=parameters,
            progress_callback=update_progress
        )
        
        # Atualizar task_id no resultado
        result.task_id = task_id
        
        # Marcar como completada
        task_manager.update_task(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            stage=TrainingStage.SAVING,
            message="Treinamento concluído com sucesso!"
        )
        
        # Armazenar resultado na task (extensão do TrainingStatus)
        task = task_manager.get_task_status(task_id)
        if task:
            # Adicionar resultado ao objeto task (workaround)
            task.result = result
        
    except HTTPException as e:
        # Erro HTTP (já formatado)
        error_msg = str(e.detail if hasattr(e, 'detail') else e)
        task_manager.update_task(
            task_id=task_id,
            status=TaskStatus.FAILED,
            progress=0,
            message="Treinamento falhou",
            error=error_msg
        )
    except Exception as e:
        # Erro inesperado
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        task_manager.update_task(
            task_id=task_id,
            status=TaskStatus.FAILED,
            progress=0,
            message="Erro inesperado durante treinamento",
            error=error_msg
        )


@router.get("/status/{task_id}", response_model=TrainingStatus)
async def get_training_status(task_id: str):
    """
    Consulta status de uma tarefa de treinamento.
    
    Retorna informações atualizadas sobre o progresso do treinamento.
    """
    task = task_manager.get_task_status(task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TASK_NOT_FOUND",
                "message": f"Task {task_id} não encontrada"
            }
        )
    
    return task


@router.get("/result/{task_id}", response_model=TrainingResult)
async def get_training_result(task_id: str):
    """
    Retorna resultado completo de um treinamento concluído.
    
    Deve ser chamado apenas quando o status for 'completed'.
    """
    task = task_manager.get_task_status(task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TASK_NOT_FOUND",
                "message": f"Task {task_id} não encontrada"
            }
        )
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "TASK_NOT_COMPLETED",
                "message": f"Task ainda não foi concluída. Status atual: {task.status}",
                "current_status": task.model_dump()
            }
        )
    
    # Retornar resultado armazenado
    if hasattr(task, 'result'):
        return task.result
    else:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "RESULT_NOT_AVAILABLE",
                "message": "Resultado do treinamento não disponível"
            }
        )


@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """
    Remove uma task do gerenciador.
    
    Útil para limpar tasks antigas depois de obter o resultado.
    """
    task = task_manager.get_task_status(task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TASK_NOT_FOUND",
                "message": f"Task {task_id} não encontrada"
            }
        )
    
    task_manager.remove_task(task_id)
    
    return {
        "status": "success",
        "message": f"Task {task_id} removida com sucesso"
    }
