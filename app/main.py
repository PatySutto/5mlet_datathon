"""Aplicação principal FastAPI para Treinamento de Modelos de Classificação de Pedras."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path

from app.config import settings
from app.routers import training, health
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

# Criar diretórios necessários
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Inicializar FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="API para treinamento e predição de classificação de pedras usando XGBoost",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Registrar exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Configurar templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Incluir routers
app.include_router(health.router)
app.include_router(training.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Página inicial com interface de treinamento.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION
        }
    )


@app.on_event("startup")
async def startup_event():
    """
    Event handler executado na inicialização da aplicação.
    """
    print("=" * 70)
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    print("=" * 70)
    print(f"📂 Upload directory: {settings.UPLOAD_DIR}")
    print(f"🤖 Model directory: {settings.MODEL_DIR}")
    print(f"📊 Docs available at: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Event handler executado no encerramento da aplicação.
    """
    print("\n👋 Encerrando aplicação...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
