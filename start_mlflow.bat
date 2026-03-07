@echo off
echo ========================================
echo   Iniciando MLflow UI
echo ========================================
echo.
echo MLflow UI estara disponivel em:
echo   http://localhost:5000
echo.
echo Pressione Ctrl+C para parar o servidor
echo ========================================
echo.

python -m mlflow ui --host 0.0.0.0 --port 5000
