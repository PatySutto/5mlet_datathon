# Datathon Passos Mágicos - Classificação de Pedras

Sistema de classificação de alunos em categorias (pedras) baseado em índices de desempenho educacional usando XGBoost.

## 🎯 Treinamento do Modelo

### Uso Básico

Para treinar o modelo XGBoost com parâmetros padrão:

```bash
python src/train.py
```

### Parâmetros Configuráveis

O script permite ajustar os principais hiperparâmetros do XGBoost:

#### Parâmetros do Modelo

- `--max-depth`: Profundidade máxima das árvores (padrão: 6, range: 3-10)
- `--n-estimators`: Número de árvores/boosting rounds (padrão: 100, range: 50-500)
- `--learning-rate`: Taxa de aprendizado (padrão: 0.1, range: 0.01-0.3)

#### Parâmetros de Treinamento

- `--test-size`: Proporção dos dados para teste (padrão: 0.2, range: 0.1-0.3)
- `--random-state`: Seed para reprodutibilidade (padrão: 42)

#### Opções de Execução

- `--no-save`: Não salva o modelo (útil para testes rápidos)
- `--grid-search`: Ativa busca em grade para encontrar melhores hiperparâmetros

### Exemplos de Treinamento

```bash
# Treino com parâmetros padrão
python src/train.py

# Treino com parâmetros customizados
python src/train.py --max-depth 8 --n-estimators 200 --learning-rate 0.05

# Teste rápido sem salvar modelo
python src/train.py --max-depth 4 --no-save

# Treino com test split maior
python src/train.py --test-size 0.25
```

### Grid Search - Busca de Hiperparâmetros

O grid search testa automaticamente múltiplas combinações de parâmetros para encontrar a melhor configuração:

```bash
# Grid search simples (4 combinações)
python src/train.py --grid-search \
  --max-depth-range "4,6,8" \
  --n-estimators-range "50,100"

# Grid search completo (18 combinações)
python src/train.py --grid-search \
  --max-depth-range "4,6,8" \
  --n-estimators-range "50,100,200" \
  --learning-rate-range "0.05,0.1,0.2"

# Grid search sem salvar (para experimentação)
python src/train.py --grid-search \
  --max-depth-range "4,6" \
  --n-estimators-range "50,100" \
  --no-save
```

O grid search:
- Testa todas as combinações de parâmetros fornecidos
- Avalia cada modelo no conjunto de teste
- Exibe ranking dos top 5 resultados
- Salva apenas o melhor modelo encontrado (se não usar `--no-save`)
- Adiciona sufixo `_gridsearch` aos arquivos salvos

### Modelos Salvos

Os modelos treinados são salvos em `app/modelo/` com a data atual:

```
app/modelo/
├── xgboost_pedra_classifier_2026-03-07.joblib
├── label_encoder_2026-03-07.pkl
└── feature_names_2026-03-07.pkl
```

Modelos de grid search têm sufixo adicional:
```
xgboost_pedra_classifier_2026-03-07_gridsearch.joblib
```

## 🔮 Predição com Modelo Treinado

### Uso Básico

Para fazer predições em novos dados, use o script `src/predict.py`:

```bash
python src/predict.py --input dados.xlsx --output predictions.csv
```

### Formato do Arquivo de Entrada

O arquivo Excel deve conter as seguintes colunas obrigatórias:

- **IPV** - Índice de Ponto de Virada
- **IPS** - Índice de Psicopedagógico
- **IAN** - Índice de Adequação de Nível
- **IEG** - Índice de Engajamento
- **INDE** - Índice de Desenvolvimento
- **IAA** - Índice de Auto-Avaliação
- **IDA** - Índice de Desempenho Acadêmico

### Saída

O arquivo CSV de saída contém:

- **Dados originais**: Todas as colunas do arquivo de entrada
- **PEDRA_PREDITA**: Classificação predita (Ametista, Esmeralda, Onix, Quartzo, Rubi, Safira, Topazio, Turmalina)
- **PROB_[classe]**: Probabilidade para cada uma das 8 classes
- **CONFIANCA**: Confiança da predição (probabilidade máxima)

### Exemplos

```bash
# Predição básica
python src/predict.py --input meus_dados.xlsx

# Especificar arquivo de saída
python src/predict.py --input dados.xlsx --output resultados.csv

# Usar modelo de diretório alternativo
python src/predict.py --input dados.xlsx --models-path caminho/para/modelo
```

### Tratamento de Dados

- **Valores faltantes**: Linhas com pelo menos 2 features válidas terão os valores faltantes preenchidos com 0
- **Linhas rejeitadas**: Linhas com menos de 2 features válidas são rejeitadas
- **Avisos**: O script informa sobre valores preenchidos ou convertidos

### Opções

```
--input, -i       Caminho para arquivo Excel de entrada (obrigatório)
--output, -o      Caminho para arquivo CSV de saída (padrão: predictions.csv)
--models-path     Diretório dos artefatos do modelo (padrão: app/modelo)
--help, -h        Exibir ajuda
```

## 📂 Estrutura do Projeto

```
src/
├── train.py               # Treinamento com parâmetros configuráveis ✨
├── predict.py             # Script de predição ✨
├── evaluate.py            # Avaliação do modelo
├── preprocessing.py       # Pré-processamento de dados
├── feature_engineering.py # Engenharia de features
└── utils.py               # Funções utilitárias

app/
└── modelo/                # Artefatos dos modelos treinados
    ├── xgboost_pedra_classifier_*.joblib
    ├── label_encoder_*.pkl
    └── feature_names_*.pkl
```

## 🚀 Início Rápido

1. Instalar dependências:
```bash
pip install -r requirements.txt
```

2. Treinar modelo (opcional - já existe um pré-treinado):
```bash
# Com parâmetros padrão
python src/train.py

# Ou experimentar com diferentes parâmetros
python src/train.py --max-depth 8 --n-estimators 200
```

3. Fazer predições com dados de exemplo:
```bash
python src/predict.py --input src/bases/dados_pedras_baixo_erro.xlsx --output predictions.csv
```

4. Visualizar resultados:
```bash
# No PowerShell
Import-Csv predictions.csv | Select-Object -First 5 | Format-Table

# Ou abrir o arquivo CSV no Excel
```

## 💡 Dicas de Uso

### Experimentando com Hiperparâmetros

Para encontrar a melhor configuração do modelo:

```bash
# 1. Teste rápido com diferentes profundidades
python src/train.py --grid-search --max-depth-range "4,6,8" --no-save

# 2. Quando encontrar bons valores, treine e salve
python src/train.py --max-depth 8 --n-estimators 200

# 3. Use o modelo salvo para predições
python src/predict.py --input novos_dados.xlsx
```

### Workflow Recomendado

1. **Exploração**: Use `--grid-search` com `--no-save` para testar rapidamente
2. **Treinamento Final**: Treine com os melhores parâmetros encontrados (sem `--no-save`)
3. **Predição**: Use o modelo mais recente em `app/modelo/`
4. **Iteração**: Se a acurácia for baixa, ajuste parâmetros e retreine
