# Docker - Guia de Deploy

## 🐳 Visão Geral

Este projeto inclui configuração Docker completa para deploy em produção, com:

- ✅ Dockerfile multi-stage (otimizado)
- ✅ docker-compose.yml (API + MLflow UI)
- ✅ .dockerignore (build rápido)
- ✅ Healthcheck configurado
- ✅ Usuário não-root (segurança)

## 📦 Arquivos Docker

### 1. Dockerfile

**Multi-stage build:**
- **Stage 1 (builder):** Instala dependências com gcc/g++
- **Stage 2 (runtime):** Imagem final slim (~500MB vs 1.5GB)

**Recursos:**
- Base: `python:3.10-slim`
- Usuário: `appuser` (não-root)
- Porta: `8000`
- Healthcheck: Verifica `/health` a cada 30s

### 2. docker-compose.yml

**Serviços:**

**api:**
- Build local do Dockerfile
- Porta: `8000:8000`
- Volumes: MLflow, uploads, modelos, dados Feast
- Restart: `unless-stopped`

**mlflow:**
- Imagem: `python:3.10-slim`
- Porta: `5000:5000`
- UI do MLflow
- Compartilha dados com API

**Rede:**
- `ml-network` (bridge)

## 🚀 Como Usar

### Opção 1: Docker Build

```bash
# Build da imagem
docker build -t pedras-ml-api:latest .

# Rodar container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/mlruns:/app/mlruns \
  -v $(pwd)/uploads:/app/uploads \
  --name pedras-api \
  pedras-ml-api:latest

# Verificar logs
docker logs -f pedras-api

# Parar e remover
docker stop pedras-api
docker rm pedras-api
```

### Opção 2: Docker Compose (Recomendado)

```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver apenas logs da API
docker-compose logs -f api

# Ver apenas logs do MLflow
docker-compose logs -f mlflow

# Parar serviços
docker-compose down

# Rebuild após mudanças de código
docker-compose up -d --build
```

## 🔍 Verificação

### Health Check

```bash
# Dentro do container
docker exec pedras-api curl http://localhost:8000/health

# Do host
curl http://localhost:8000/api/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "models_available": 1
}
```

### Acessar Serviços

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **MLflow UI:** http://localhost:5000

## 📊 Volumes Persistidos

```yaml
volumes:
  - ./mlruns:/app/mlruns              # Experimentos MLflow
  - ./mlflow_artifacts:/app/mlflow_artifacts  # Artefatos
  - ./uploads:/app/uploads            # Upload de dados
  - ./results:/app/results            # Resultados de batch
  - ./app/modelo:/app/app/modelo      # Modelos treinados
  - ./src/data:/app/src/data          # Registry Feast
  - ./src/bases:/app/src/bases        # Dados processados
```

## 🛠️ Comandos Úteis

### Entrar no container

```bash
docker exec -it pedras-api bash
```

### Ver recursos consumidos

```bash
docker stats pedras-api
```

### Limpar volumes

```bash
# CUIDADO: Remove todos os dados
docker-compose down -v
```

### Rebuild completo

```bash
# Remove cache e reconstrói
docker-compose build --no-cache
docker-compose up -d
```

## 🔧 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker logs pedras-api

# Ver últimas 100 linhas
docker logs --tail 100 pedras-api
```

### Healthcheck falhando

```bash
# Verificar status de health
docker inspect pedras-api | grep -A 10 Health

# Testar manualmente
docker exec pedras-api curl http://localhost:8000/api/health
```

### Porta já em uso

```bash
# Verificar o que está usando a porta
netstat -ano | findstr :8000

# Mudar porta no docker-compose.yml
ports:
  - "8080:8000"  # Host:Container
```

### Volumes não persistindo

```bash
# Verificar permissões
docker exec pedras-api ls -la /app/mlruns

# Recriar volumes
docker-compose down -v
docker-compose up -d
```

## 🔒 Segurança

**Implementado:**
- ✅ Usuário não-root (`appuser`)
- ✅ Imagem slim (menor superfície de ataque)
- ✅ Multi-stage build (não inclui gcc/g++ na imagem final)
- ✅ .dockerignore (não copia .git, venv, etc.)

**Recomendações para produção:**
- [ ] Usar secrets para configurações sensíveis
- [ ] Implementar rate limiting
- [ ] Adicionar autenticação JWT
- [ ] Usar HTTPS com certificado SSL
- [ ] Scan de vulnerabilidades: `docker scan pedras-ml-api`

## 📈 Otimizações

### Build mais rápido

```bash
# Usar buildkit
DOCKER_BUILDKIT=1 docker build -t pedras-ml-api .
```

### Imagem menor

Tamanho atual: ~500MB

Para reduzir mais:
- Usar `python:3.10-alpine` (mais complexo)
- Remover cache do pip
- Usar requirements.txt mínimo

### Cache de layers

O Dockerfile está otimizado para cache:
1. Copia requirements.txt primeiro
2. Instala dependências (layer cacheado)
3. Copia código depois

Mudanças no código NÃO reinstalam dependências.

## 🌐 Deploy em Cloud

### AWS ECS

```bash
# Login no ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

# Tag e push
docker tag pedras-ml-api:latest <account>.dkr.ecr.us-east-1.amazonaws.com/pedras-ml-api:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/pedras-ml-api:latest
```

### Google Cloud Run

```bash
# Build e push
gcloud builds submit --tag gcr.io/<project-id>/pedras-ml-api

# Deploy
gcloud run deploy pedras-ml-api \
  --image gcr.io/<project-id>/pedras-ml-api \
  --platform managed \
  --port 8000
```

### Azure Container Instances

```bash
# Login no ACR
az acr login --name <registry-name>

# Tag e push
docker tag pedras-ml-api:latest <registry-name>.azurecr.io/pedras-ml-api:latest
docker push <registry-name>.azurecr.io/pedras-ml-api:latest

# Deploy
az container create \
  --name pedras-ml-api \
  --image <registry-name>.azurecr.io/pedras-ml-api:latest \
  --ports 8000
```

## 📝 Notas

- MLflow UI demora ~10s para iniciar (instala MLflow no primeiro boot)
- Modelos treinados persistem em volumes
- Feast registry persiste em `src/data/registry.db`
- Logs são escritos no stdout (visíveis com `docker logs`)

## ✅ Checklist de Deploy

Antes de fazer deploy em produção:

- [ ] Build da imagem funciona: `docker build -t pedras-ml-api .`
- [ ] Container inicia: `docker-compose up -d`
- [ ] Health check passa: `curl http://localhost:8000/api/health`
- [ ] API Docs acessível: http://localhost:8000/docs
- [ ] MLflow UI acessível: http://localhost:5000
- [ ] Volumes persistem após restart
- [ ] Testes passam: `docker exec pedras-api pytest tests/`
- [ ] Logs não mostram erros
- [ ] Recursos adequados (CPU/Memory)

---

**Última Atualização:** 2026-03-07  
**Versão:** 1.0  
**Status:** ✅ Produção-Ready
