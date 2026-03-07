# Datathon Passos Mágicos - Classificação de Pedras

Sistema de classificação de alunos em categorias (pedras) baseado em índices de desempenho educacional usando XGBoost.

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
├── predict.py              # Script de predição (novo!)
├── train.py               # Treinamento do modelo
├── evaluate.py            # Avaliação do modelo
├── preprocessing.py       # Pré-processamento de dados
├── feature_engineering.py # Engenharia de features
└── utils.py              # Funções utilitárias

app/
└── modelo/               # Artefatos do modelo treinado
    ├── xgboost_pedra_classifier_*.joblib
    ├── label_encoder_*.pkl
    └── feature_names_*.pkl
```

## 🚀 Início Rápido

1. Instalar dependências:
```bash
pip install -r requirements.txt
```

2. Fazer predições com dados de exemplo:
```bash
python src/predict.py --input src/bases/dados_pedras_baixo_erro.xlsx --output predictions.csv
```

3. Visualizar resultados:
```bash
# No PowerShell
Import-Csv predictions.csv | Select-Object -First 5 | Format-Table

# Ou abrir o arquivo CSV no Excel
```
