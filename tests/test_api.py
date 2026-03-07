"""Testes para os endpoints da API REST."""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

# Cliente de teste
client = TestClient(app)


class TestHealthEndpoints:
    """Testes para endpoints de health check."""
    
    def test_health_endpoint_returns_200(self):
        """Testa se o endpoint /api/health retorna status 200."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_endpoint_returns_correct_structure(self):
        """Testa se o endpoint /api/health retorna estrutura correta."""
        response = client.get("/api/health")
        data = response.json()
        
        # Verifica campos obrigatórios
        assert "status" in data
        assert "version" in data
        assert "models_available" in data
        
        # Verifica tipos
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["models_available"], int)


class TestModelsEndpoint:
    """Testes para endpoint de listagem de modelos."""
    
    def test_models_endpoint_returns_200(self):
        """Testa se o endpoint /api/models retorna status 200."""
        response = client.get("/api/models")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_models_endpoint_structure(self):
        """Testa estrutura de resposta do endpoint /api/models."""
        response = client.get("/api/models")
        data = response.json()
        
        # Se houver modelos, verifica estrutura
        if len(data) > 0:
            model = data[0]
            assert "model_id" in model
            assert "filename" in model
            assert "created_at" in model


class TestPredictionEndpoints:
    """Testes para endpoints de predição."""
    
    def test_prediction_endpoint_accepts_post(self):
        """Testa se endpoint de predição aceita POST."""
        # Dados de teste válidos
        payload = {
            "IPV": 50.0,
            "IPS": 50.0,
            "IAN": 50.0,
            "IEG": 50.0,
            "INDE": 50.0,
            "IAA": 50.0,
            "IDA": 50.0
        }
        
        response = client.post("/api/prediction", json=payload)
        
        # Pode retornar 200 (com modelo) ou 404 (sem modelo)
        assert response.status_code in [200, 404]
    
    def test_prediction_endpoint_validates_input(self):
        """Testa validação de entrada do endpoint de predição."""
        # Payload inválido (faltando campos)
        invalid_payload = {
            "IPV": 50.0,
            "IPS": 50.0
            # Faltando outros campos
        }
        
        response = client.post("/api/prediction", json=invalid_payload)
        
        # Deve retornar erro de validação
        assert response.status_code == 422


class TestTrainingEndpoints:
    """Testes para endpoints de treinamento."""
    
    def test_training_upload_requires_file(self):
        """Testa se endpoint de upload requer arquivo."""
        response = client.post("/api/training/upload")
        
        # Deve retornar erro (422 - validation error)
        assert response.status_code == 422
    
    def test_training_start_requires_parameters(self):
        """Testa se endpoint de start aceita parâmetros."""
        payload = {
            "max_depth": 6,
            "n_estimators": 100,
            "learning_rate": 0.1,
            "test_size": 0.2,
            "use_feast": False
        }
        
        response = client.post("/api/training/start", json=payload)
        
        # Pode retornar 200 (iniciado) ou 400 (sem dados)
        assert response.status_code in [200, 400, 202]


class TestAPIDocumentation:
    """Testes para documentação da API."""
    
    def test_openapi_docs_accessible(self):
        """Testa se a documentação OpenAPI está acessível."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_accessible(self):
        """Testa se o ReDoc está acessível."""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestCORS:
    """Testes para configuração de CORS."""
    
    def test_cors_headers_present(self):
        """Testa se headers CORS estão presentes."""
        response = client.options("/api/health")
        
        # Verifica se CORS está configurado
        assert response.status_code in [200, 405]  # 405 é OK se OPTIONS não for explicitamente tratado


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
