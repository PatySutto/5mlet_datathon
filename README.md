# 🔮 Datathon Passos Mágicos - Classificação de Pedras

[![CI/CD Pipeline](https://github.com/USERNAME/dt-2/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/dt-2/actions/workflows/ci.yml)

Sistema de Machine Learning para classificação de alunos em categorias (pedras preciosas) baseado em índices de desempenho educacional usando XGBoost, FastAPI e Feast Feature Store.

## 📋 Requisitos

- **Python 3.14+**
- Docker Desktop (opcional, para execução em container)

## 📂 Estrutura do Projeto

```
dt-2/
├── app/                              # Aplicação FastAPI
│   ├── main.py                       # Entry point da API
│   ├── routes.py                     # Rotas principais
│   ├── model/                        # (deprecated)
│   ├── modelo/                       # Modelos treinados (.joblib)
│   ├── routers/                      # Routers modulares da API
│   │   ├── health.py                 # Endpoints de health/info/models
│   │   ├── prediction.py             # Endpoints de predição
│   │   └── training.py               # Endpoints de treinamento
│   ├── schemas/                      # Pydantic schemas
│   ├── static/                       # Frontend (HTML/CSS/JS)
│   └── config.py                     # Configurações da aplicação
│
├── src/                              # Scripts de ML
│   ├── train.py                      # Treinamento de modelos
│   ├── evaluate.py                   # Avaliação de modelos
│   ├── preprocessing.py              # Pré-processamento de dados
│   ├── feature_engineering.py        # Feast Feature Store
│   ├── feature_store.yaml            # Configuração do Feast
│   ├── utils.py                      # Utilitários
│   ├── data/                         # Datasets brutos
│   └── bases/                        # Dados processados
│       ├── treated/                  # Dados limpos
│       └── features/                 # Features do Feast
│
├── tests/                            # Testes automatizados
│   ├── test_preprocessing.py         # Testes de pré-processamento
│   ├── test_model.py                 # Testes de modelagem
│   └── test_api.py                   # Testes de API
│
├── mlruns/                           # Tracking do MLflow
├── mlflow_artifacts/                 # Artefatos do MLflow
├── notebooks/                        # Jupyter notebooks
│   └── DATATHON-PASSOS-MÁGICOS.ipynb
│
├── Dockerfile                        # Build da imagem Docker
├── docker-compose.yml                # Orquestração de containers
├── .dockerignore                     # Exclusões do Docker
├── requirements.txt                  # Dependências Python
└── README.md                         # Este arquivo
```

## 🚀 Como Executar

### Opção 1: Terminal (Desenvolvimento)

1. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

2. **Iniciar a aplicação:**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. **Acessar:**
- Interface: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Opção 2: Docker (Produção)

1. **Iniciar Docker Desktop** (Windows)

2. **Buildar e iniciar containers:**
```bash
docker-compose up -d --build
```

3. **Verificar status:**
```bash
docker-compose ps
```

4. **Acessar:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MLflow UI: http://localhost:5000

5. **Ver logs:**
```bash
docker-compose logs -f api
```

6. **Parar aplicação:**
```bash
docker-compose down
```

## 🎯 Funcionalidades Principais

### 1. Treinamento de Modelos
```bash
# Treino com parâmetros padrão
python src/train.py

# Treino com GridSearch
python src/train.py --grid-search

# Treino com Feast Feature Store
python src/train.py --use-feast
```

### 2. Predição via API
- **Single Prediction**: Predição individual com 7 features
- **Batch Prediction**: Upload de Excel para predições em lote
- **Model Selection**: Escolha entre modelos treinados

### 3. MLflow Tracking
Todos os treinamentos são rastreados automaticamente com:
- Hiperparâmetros
- Métricas (accuracy, F1, precision, recall)
- Artefatos (modelos, classification reports)

## 🧪 Testes

Executar testes automatizados:
```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app --cov=src --cov-report=term-missing

# Apenas testes unitários
pytest tests/test_preprocessing.py tests/test_model.py -v
```

## 🔄 CI/CD

O projeto usa **GitHub Actions** para integração e entrega contínuas.

### Pipeline Automatizado
Executa automaticamente em cada push ou pull request:
- ✅ **Testes**: Pytest com cobertura de código
- ✅ **Qualidade**: Análise de código com flake8
- ✅ **Relatórios**: Upload automático para Codecov

### Status do Build
[![CI/CD Pipeline](https://github.com/USERNAME/dt-2/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/dt-2/actions/workflows/ci.yml)

**Nota:** Substitua `USERNAME` pelo seu usuário do GitHub para ativar o badge.

Consulte [CI_CD_GUIDE.md](CI_CD_GUIDE.md) para configuração detalhada.

## 📊 Features do Modelo

As 7 features utilizadas para classificação:
1. **INDE** - Índice de Desenvolvimento Educacional
2. **IAA** - Índice de Auto-Avaliação
3. **IEG** - Índice de Engajamento
4. **IPS** - Índice Psicossocial
5. **IDA** - Índice de Desenvolvimento Acadêmico
6. **IPP** - Índice Psicopedagógico
7. **IPV** - Índice de Ponto de Virada

## 🔧 Tecnologias

- **ML**: XGBoost, Scikit-learn, MLflow
- **Feature Store**: Feast
- **API**: FastAPI, Uvicorn
- **Frontend**: HTML5, JavaScript, Bootstrap
- **Containerização**: Docker, Docker Compose
- **Testes**: Pytest, Pytest-cov
- **CI/CD**: GitHub Actions

## 📝 Documentação Adicional

- [CI_CD_GUIDE.md](CI_CD_GUIDE.md) - Guia de CI/CD com GitHub Actions
- [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Guia completo do Docker
- [FEAST_INTEGRATION.md](FEAST_INTEGRATION.md) - Integração com Feast
- [MLFLOW_GUIDE.md](MLFLOW_GUIDE.md) - Uso do MLflow

---

**Desenvolvido para o Datathon Passos Mágicos 2026**
