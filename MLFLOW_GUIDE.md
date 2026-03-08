# Como usar o MLflow UI

## 🚀 Iniciando o MLflow UI

### Opção 1: Usando o script (RECOMENDADO)
```bash
# No Windows
.\start_mlflow.bat
```

### Opção 2: Manual
```bash
mlflow ui --host 0.0.0.0 --port 5000
```

## 📊 Acessando

Após iniciar, acesse:
- **URL Local:** http://localhost:5000
- **Link na Interface:** Clique no botão "📈 MLflow UI" no canto superior direito da aplicação

## 📋 O que você verá no MLflow UI

### Experimentos
- **pedras_classification** - Todos os treinamentos realizados

### Informações de cada Run
- ✅ **Métricas:** Accuracy, Precision, Recall, F1-Score (por classe)
- ⚙️ **Parâmetros:** max_depth, n_estimators, learning_rate, test_size, etc.
- 📦 **Artefatos:** 
  - `classification_report.txt` - Relatório detalhado
  - `confusion_matrix.png` - Matriz de confusão
  - `feature_importance.png` - Importância das features
  - Modelo XGBoost exportado

### Comparação de Modelos
- Compare múltiplos runs lado a lado
- Visualize gráficos de métricas
- Identifique o melhor modelo

## 🛑 Parando o MLflow UI

Pressione `Ctrl + C` no terminal onde o MLflow está rodando.

## 📁 Localização dos Dados

Os dados do MLflow estão armazenados em:
```
mlruns/
├── 0/                          # Experimento padrão
├── 845474572462031039/         # Experimento pedras_classification
│   ├── aeecabb.../             # Run 1
│   ├── f7fe5fe.../             # Run 2
│   └── models/                 # Modelos registrados
```

## 💡 Dicas

1. **Mantenha o MLflow rodando** enquanto treina modelos para ver atualizações em tempo real
2. **Compare modelos** usando a funcionalidade de comparação do MLflow
3. **Registre modelos** importantes para deployment futuro
4. **Exporte métricas** para análise externa

## 🔗 Links Úteis

- [MLflow Documentation](https://www.mlflow.org/docs/latest/index.html)
- [MLflow Tracking](https://www.mlflow.org/docs/latest/tracking.html)
- [MLflow Model Registry](https://www.mlflow.org/docs/latest/model-registry.html)
