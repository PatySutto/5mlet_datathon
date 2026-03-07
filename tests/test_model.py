"""Testes para o módulo de treinamento do modelo."""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Adiciona o diretório src ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from train import load_data_for_training, train_model


class TestModel:
    """Testes para funções de treinamento do modelo."""
    
    def test_load_data_returns_correct_format(self):
        """Testa se load_data_for_training retorna X e y no formato correto."""
        # Arrange & Act
        X, y = load_data_for_training(use_feast=False)
        
        # Assert
        assert isinstance(X, pd.DataFrame), "X deve ser um DataFrame"
        assert isinstance(y, pd.Series), "y deve ser uma Series"
        assert len(X) == len(y), "X e y devem ter o mesmo número de linhas"
        
        # Verifica features esperadas
        expected_features = ['IPV', 'IPS', 'IAN', 'IEG', 'INDE', 'IAA', 'IDA']
        assert list(X.columns) == expected_features, f"Features devem ser {expected_features}"
        
        # Verifica que não há valores nulos
        assert not X.isnull().any().any(), "X não deve conter valores nulos"
        assert not y.isnull().any(), "y não deve conter valores nulos"
    
    def test_train_model_returns_valid_model(self):
        """Testa se train_model retorna um modelo treinado válido."""
        # Arrange
        X, y = load_data_for_training(use_feast=False)
        
        # Act
        model, encoder, X_test, y_test, X_train, y_train = train_model(
            X, y,
            max_depth=4,
            n_estimators=50,
            learning_rate=0.1,
            test_size=0.2,
            random_state=42,
            verbose=False
        )
        
        # Assert
        assert model is not None, "Modelo não deve ser None"
        assert hasattr(model, 'predict'), "Modelo deve ter método predict"
        assert encoder is not None, "Encoder não deve ser None"
        
        # Verifica que o modelo pode fazer predições
        predictions = model.predict(X_test)
        assert len(predictions) == len(X_test), "Predições devem ter mesmo tamanho que X_test"
        assert predictions.min() >= 0, "Predições devem ser >= 0"
        assert predictions.max() < len(encoder.classes_), "Predições devem estar no range das classes"
        
        # Verifica divisão treino/teste
        assert len(X_train) > len(X_test), "Conjunto de treino deve ser maior que teste"
        assert len(X_train) + len(X_test) == len(X), "Soma de treino e teste deve igualar total"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
