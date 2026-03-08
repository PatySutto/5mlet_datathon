# Dockerfile multi-stage para o projeto de ML Engineering
# Stage 1: Builder - instala dependências
FROM python:3.14-slim as builder

# Instala dependências do sistema necessárias para compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia arquivo de requirements
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - imagem final mais leve
FROM python:3.14-slim

# Metadados da imagem
LABEL maintainer="Datathon Team"
LABEL description="API de Machine Learning para classificação de pedras"
LABEL version="1.0"

# Instala apenas dependências de runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root para segurança
RUN useradd -m -u 1000 appuser

# Define diretório de trabalho
WORKDIR /app

# Copia dependências instaladas do builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copia código da aplicação
COPY --chown=appuser:appuser . .

# Cria diretórios necessários com permissões corretas
RUN mkdir -p /app/uploads /app/results /app/src/data /app/mlruns && \
    chown -R appuser:appuser /app

# Muda para usuário não-root
USER appuser

# Expõe porta da API
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando para iniciar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]