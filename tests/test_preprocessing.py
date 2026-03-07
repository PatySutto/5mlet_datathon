"""Testes para o módulo de preprocessing."""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Adiciona o diretório src ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from preprocessing import load_and_preprocess_data


class TestPreprocessing:
    """Testes para funções de preprocessing."""
    
    def test_load_and_preprocess_returns_dataframe(self):
        """Testa se load_and_preprocess_data retorna um DataFrame."""
        # Arrange & Act
        df = load_and_preprocess_data(save_output=False)
        
        # Assert
        assert isinstance(df, pd.DataFrame), "Deve retornar um DataFrame"
        assert len(df) > 0, "DataFrame não deve estar vazio"
        assert 'PEDRA' in df.columns, "Deve conter coluna PEDRA"
    
    def test_student_id_column_added(self):
        """Testa se a coluna student_id é adicionada corretamente."""
        # Arrange & Act
        df = load_and_preprocess_data(save_output=False)
        
        # Assert
        assert 'student_id' in df.columns, "Deve conter coluna student_id"
        assert df['student_id'].iloc[0] == 0, "Primeiro student_id deve ser 0"
        assert df['student_id'].iloc[-1] == len(df) - 1, "Último student_id deve ser len(df)-1"
        assert df['student_id'].is_monotonic_increasing, "student_id deve ser sequencial crescente"
        assert df['student_id'].nunique() == len(df), "student_id deve ser único para cada linha"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
