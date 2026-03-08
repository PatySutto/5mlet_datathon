"""Serviço para gerenciar uploads de arquivos."""

import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import Tuple

from app.config import settings


async def validate_upload_file(file: UploadFile) -> None:
    """
    Valida o arquivo enviado.
    
    Args:
        file: Arquivo enviado
        
    Raises:
        HTTPException: Se arquivo inválido
    """
    # Validar content type
    if file.content_type not in settings.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo inválido: {file.content_type}. "
                   f"Tipos permitidos: {', '.join(settings.ALLOWED_CONTENT_TYPES)}"
        )
    
    # Validar extensão do arquivo
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensão de arquivo inválida: {file_ext}. "
                   f"Extensões permitidas: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Ler e validar tamanho sem carregar tudo na memória
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo muito grande. Tamanho máximo: "
                       f"{settings.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB"
            )
    
    # Reset file pointer para leitura posterior
    await file.seek(0)


async def save_upload_file(file: UploadFile) -> Tuple[str, Path]:
    """
    Salva arquivo enviado com nome único.
    
    Args:
        file: Arquivo enviado
        
    Returns:
        Tupla (file_id, file_path)
    """
    # Gerar ID único
    file_id = str(uuid.uuid4())
    
    # Obter extensão original
    file_ext = Path(file.filename).suffix
    
    # Criar path seguro
    file_path = settings.UPLOAD_DIR / f"{file_id}{file_ext}"
    
    # Salvar arquivo de forma assíncrona
    async with aiofiles.open(file_path, 'wb') as f:
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            await f.write(chunk)
    
    return file_id, file_path


async def cleanup_upload(file_path: Path) -> None:
    """
    Remove arquivo temporário após processamento.
    
    Args:
        file_path: Caminho do arquivo a remover
    """
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        # Log erro mas não falha a operação
        print(f"Aviso: Não foi possível remover arquivo temporário {file_path}: {e}")


def get_safe_filename(filename: str) -> str:
    """
    Retorna nome de arquivo seguro (sem caracteres perigosos).
    
    Args:
        filename: Nome original do arquivo
        
    Returns:
        Nome seguro
    """
    # Remove caracteres perigosos
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    safe_name = "".join(c if c in safe_chars else "_" for c in filename)
    
    # Limita tamanho
    if len(safe_name) > 200:
        name_part = safe_name[:180]
        ext_part = Path(safe_name).suffix
        safe_name = name_part + ext_part
    
    return safe_name
