"""Gerenciador de tasks de treinamento."""

import uuid
from datetime import datetime
from typing import Dict, Optional
from threading import Lock

from app.models.schemas import TrainingStatus, TaskStatus, TrainingStage


class TaskManager:
    """Gerenciador de tasks em memória."""
    
    def __init__(self):
        self._tasks: Dict[str, TrainingStatus] = {}
        self._lock = Lock()
    
    def create_task(self) -> str:
        """
        Cria uma nova task.
        
        Returns:
            ID da task criada
        """
        task_id = str(uuid.uuid4())
        
        with self._lock:
            self._tasks[task_id] = TrainingStatus(
                task_id=task_id,
                status=TaskStatus.PENDING,
                progress=0,
                stage=TrainingStage.UPLOAD,
                message="Task criada, aguardando início...",
                started_at=datetime.now(),
                completed_at=None,
                error=None
            )
        
        return task_id
    
    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        stage: Optional[TrainingStage] = None,
        message: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Atualiza status de uma task.
        
        Args:
            task_id: ID da task
            status: Novo status
            progress: Progresso (0-100)
            stage: Estágio atual
            message: Mensagem descritiva
            error: Mensagem de erro
        """
        with self._lock:
            if task_id not in self._tasks:
                return
            
            task = self._tasks[task_id]
            
            if status is not None:
                task.status = status
            
            if progress is not None:
                task.progress = progress
            
            if stage is not None:
                task.stage = stage
            
            if message is not None:
                task.message = message
            
            if error is not None:
                task.error = error
            
            # Se completou ou falhou, registrar timestamp
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                task.completed_at = datetime.now()
    
    def get_task_status(self, task_id: str) -> Optional[TrainingStatus]:
        """
        Retorna status de uma task.
        
        Args:
            task_id: ID da task
            
        Returns:
            TrainingStatus ou None se não encontrada
        """
        with self._lock:
            return self._tasks.get(task_id)
    
    def remove_task(self, task_id: str) -> None:
        """
        Remove uma task do gerenciador.
        
        Args:
            task_id: ID da task
        """
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
    
    def list_all_tasks(self) -> Dict[str, TrainingStatus]:
        """
        Lista todas as tasks.
        
        Returns:
            Dicionário com todas as tasks
        """
        with self._lock:
            return self._tasks.copy()
    
    def cleanup_old_tasks(self, max_age_seconds: int = 3600) -> int:
        """
        Remove tasks antigas (completadas ou falhadas).
        
        Args:
            max_age_seconds: Idade máxima em segundos
            
        Returns:
            Número de tasks removidas
        """
        now = datetime.now()
        removed = 0
        
        with self._lock:
            tasks_to_remove = []
            
            for task_id, task in self._tasks.items():
                if task.completed_at:
                    age = (now - task.completed_at).total_seconds()
                    if age > max_age_seconds:
                        tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self._tasks[task_id]
                removed += 1
        
        return removed


# Instância global do gerenciador
task_manager = TaskManager()
