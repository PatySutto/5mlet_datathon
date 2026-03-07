"""Serviço de pré-processamento de dados."""

import pandas as pd
from pathlib import Path
from datetime import datetime
from fastapi import HTTPException
from typing import Tuple

from app.config import settings
from app.models.schemas import ValidationInfo


def preprocess_uploaded_file(file_path: Path) -> Tuple[Path, ValidationInfo]:
    """
    Processa arquivo Excel enviado.
    
    Args:
        file_path: Caminho do arquivo enviado
        
    Returns:
        Tupla (treated_file_path, validation_info)
        
    Raises:
        HTTPException: Se validação falhar
    """
    try:
        # Ler arquivo Excel
        df = pd.read_excel(file_path)
        total_records = len(df)
        
        # Validar colunas obrigatórias
        missing_columns = [
            col for col in settings.REQUIRED_COLUMNS 
            if col not in df.columns
        ]
        if missing_columns:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "MISSING_COLUMNS",
                    "message": f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}",
                    "details": {
                        "missing_columns": missing_columns,
                        "required_columns": settings.REQUIRED_COLUMNS,
                        "found_columns": df.columns.tolist()
                    }
                }
            )
        
        # Remove linhas onde PEDRA está vazio
        initial_count = len(df)
        df = df.dropna(subset=['PEDRA'])
        pedra_dropped = initial_count - len(df)
        
        # Converte colunas numéricas para tipo numérico
        warnings = []
        for col in settings.FEATURE_COLUMNS:
            if col in df.columns:
                original_type = df[col].dtype
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Rastrear conversões que geraram NaN
                na_count = df[col].isna().sum()
                if na_count > 0:
                    warnings.append(
                        f"Coluna '{col}': {na_count} valor(es) inválido(s) "
                        f"convertido(s) para NaN"
                    )
        
        # Trata valores vazios nas colunas numéricas
        # Se 2 ou mais colunas numéricas estiverem preenchidas, preencher as outras com 0
        # Caso contrário, remover a linha
        numeric_filled_count = df[settings.FEATURE_COLUMNS].notna().sum(axis=1)
        valid_rows = numeric_filled_count >= 2
        
        # Conta linhas rejeitadas
        rejected_count = (~valid_rows).sum()
        if rejected_count > 0:
            warnings.append(
                f"{rejected_count} linha(s) rejeitada(s) por ter menos de 2 features válidas"
            )
        
        # Remove linhas com menos de 2 colunas numéricas preenchidas
        df = df[valid_rows].copy()
        
        # Valida se restaram dados
        if len(df) == 0:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "NO_VALID_DATA",
                    "message": "Nenhum registro válido encontrado após validação",
                    "details": {
                        "total_records": total_records,
                        "reason": "Todas as linhas têm menos de 2 features válidas"
                    }
                }
            )
        
        # Preenche valores vazios das colunas numéricas com 0
        df[settings.FEATURE_COLUMNS] = df[settings.FEATURE_COLUMNS].fillna(0)
        
        # Reset do índice após remoção de linhas
        df = df.reset_index(drop=True)
        
        # Salva o arquivo processado em bases/treated
        today = datetime.now().strftime('%Y-%m-%d')
        output_file = settings.TREATED_DATA_DIR / f'dados_pedras_processado_{today}.xlsx'
        
        # Se arquivo já existe, adiciona timestamp ao nome
        if output_file.exists():
            timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            output_file = settings.TREATED_DATA_DIR / f'dados_pedras_processado_{timestamp}.xlsx'
        
        df.to_excel(output_file, index=False)
        
        # Criar informação de validação
        validation_info = ValidationInfo(
            total_records=total_records,
            valid_records=len(df),
            rejected_records=total_records - len(df),
            warnings=warnings
        )
        
        return output_file, validation_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "PREPROCESSING_ERROR",
                "message": f"Erro ao processar arquivo: {str(e)}",
                "details": {"exception": str(type(e).__name__)}
            }
        )


def get_latest_treated_file() -> Path:
    """
    Retorna o arquivo tratado mais recente.
    
    Returns:
        Path do arquivo mais recente
        
    Raises:
        HTTPException: Se nenhum arquivo encontrado
    """
    treated_files = list(settings.TREATED_DATA_DIR.glob('*.xlsx'))
    
    if not treated_files:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "NO_TREATED_FILES",
                "message": "Nenhum arquivo tratado encontrado",
                "details": {"directory": str(settings.TREATED_DATA_DIR)}
            }
        )
    
    # Retorna o mais recente
    latest_file = max(treated_files, key=lambda x: x.stat().st_mtime)
    return latest_file
