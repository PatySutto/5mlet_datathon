# Feast Feature Store - Guia de Integração

## 🎯 Visão Geral

O Feast Feature Store foi completamente integrado ao pipeline de treinamento do projeto. Esta integração permite:

- ✅ Gerenciamento centralizado de features
- ✅ Versionamento de dados de features
- ✅ Consistência entre treinamento e inferência
- ✅ Modo híbrido (Feast + Excel legado)

## 🔧 Arquitetura Implementada

### Fluxo de Dados

```
Excel (Raw Data)
    ↓
preprocessing.py (adiciona student_id)
    ↓
bases/treated/*.xlsx (com student_id)
    ↓
feature_engineering.py (converte para Parquet)
    ↓
bases/features/pedras_features.parquet
    ↓
Feast Feature Store (entity: student, features: 7 indicadores)
    ↓
train.py (--use-feast flag)
    ↓
Modelo XGBoost treinado
```

### Componentes Modificados

#### 1. **preprocessing.py**
- **Mudança**: Adiciona coluna `student_id` sequencial (0, 1, 2, ..., N-1)
- **Motivo**: Feast precisa de entity key (não pode usar PEDRA, que é o target)
- **Localização**: Linha 60, após `reset_index()`

#### 2. **feature_engineering.py**
- **Entity Definition**: Mudou de `pedra` (PEDRA values) para `student` (student_id)
- **FeatureView**: Renomeada de `pedras_features` para `student_features`
- **Novas Funções**:
  - `get_features_for_training()`: Carrega X, y completo do Feast
  - `get_features()` atualizado para usar `student_id` em vez de `PEDRA`
- **Correções**: Adicionado `value_type=ValueType.INT64` para eliminar warnings

#### 3. **train.py**
- **Novo Parâmetro**: `--use-feast` flag (default: False)
- **Função Modificada**: `load_data_for_training(use_feast=False)`
  - Se `use_feast=True`: Carrega via Feast
  - Se `use_feast=False`: Carrega via Excel (modo legado)
- **Fallback**: Se Feast falhar, automaticamente usa modo legado

#### 4. **training_service.py**
- **Mudança**: Passa `parameters.use_feast` para `load_data_for_training()`
- **API**: Suporta `{"use_feast": true}` no POST `/api/training`

#### 5. **feature_store.yaml**
- **Atualização**: `entity_key_serialization_version: 3` (era 2)
- **Motivo**: Eliminar deprecation warning do Feast

## 📖 Como Usar

### Modo 1: Treinamento via Command Line

#### Com Feast (recomendado)
```bash
cd src
python train.py --use-feast
```

#### Sem Feast (modo legado)
```bash
cd src
python train.py
```

#### Teste rápido com Feast
```bash
cd src
python train.py --use-feast --max-depth 6 --n-estimators 100 --no-save
```

### Modo 2: Treinamento via API

#### Com Feast
```json
POST /api/training
{
    "max_depth": 6,
    "n_estimators": 100,
    "learning_rate": 0.1,
    "test_size": 0.2,
    "use_feast": true
}
```

#### Sem Feast (modo legado)
```json
POST /api/training
{
    "max_depth": 6,
    "n_estimators": 100,
    "learning_rate": 0.1,
    "test_size": 0.2,
    "use_feast": false
}
```

### Modo 3: Preparar Features Manualmente

```bash
cd src

# 1. Preprocessing (adiciona student_id)
python preprocessing.py

# 2. Feature Engineering (cria Feast Feature Store)
python feature_engineering.py

# 3. Treinar com Feast
python train.py --use-feast
```

## 🔍 Verificação e Testes

### Verificar student_id foi adicionado
```bash
cd src
python preprocessing.py
# Verificar output: deve mostrar "student_id" como primeira coluna
```

### Testar Feast Feature Store
```bash
cd src
python feature_engineering.py
# Output esperado:
# ✅ student_id column verified
# Feature Store inicializado com sucesso!
# Testa recuperação de features...
```

### Comparar Feast vs Excel (Validação)
Ambos devem treinar com sucesso:
```bash
cd src

# Treinar com Feast
python train.py --use-feast --no-save

# Treinar com Excel
python train.py --no-save
```

## 📊 Estrutura de Dados

### Arquivo Treated (Excel)
| student_id | PEDRA     | IPV  | IPS  | IAN   | IEG   | INDE | IAA   | IDA  |
|------------|-----------|------|------|-------|-------|------|-------|------|
| 0          | Esmeralda | 72.0 | 15.0 | 17.55 | 38.10 | 89.0 | 56.66 | 26.0 |
| 1          | Esmeralda | 39.0 | 75.0 | 69.18 | 22.99 | 41.0 | 45.13 | 80.0 |
| ...        | ...       | ...  | ...  | ...   | ...   | ...  | ...   | ...  |

### Parquet Features (Feast)
- **Entity**: student_id (INT64)
- **Features**: IPV, IPS, IAN, IEG, INDE, IAA, IDA (FLOAT64)
- **Target**: PEDRA (não armazenado no Feast, apenas no parquet)
- **Timestamp**: event_timestamp (para TTL do Feast)

### Entity vs Target
- ✅ **Entity Key**: `student_id` (identificador único de cada linha/estudante)
- ❌ **NÃO usar PEDRA como entity**: PEDRA é o target a ser previsto, não um identificador

## ⚙️ Configuração do Feast

### feature_store.yaml
```yaml
project: pedras_features
registry: data/registry.db
provider: local
online_store:
    type: sqlite
    path: data/online_store.db
offline_store:
    type: file
entity_key_serialization_version: 3
```

### Arquivos Gerados
```
src/
├── data/
│   ├── registry.db          # Feast registry (metadata)
│   └── online_store.db      # SQLite online store (não usado)
├── bases/
│   ├── treated/
│   │   └── dados_pedras_processado_YYYY-MM-DD.xlsx  # Com student_id
│   └── features/
│       └── pedras_features.parquet  # Features + PEDRA + student_id
└── feature_store.yaml       # Configuração do Feast
```

## 🚨 Troubleshooting

### Erro: "Coluna 'student_id' não encontrada"
**Solução**: Execute o preprocessing novamente para adicionar student_id aos dados:
```bash
cd src
python preprocessing.py
```

### Erro: "Arquivo de features não encontrado"
**Solução**: Execute feature_engineering para criar o parquet:
```bash
cd src
python feature_engineering.py
```

### Feast retorna dados incorretos
**Solução**: Limpe o registry e recrie:
```bash
cd src
rm -rf data/registry.db
python feature_engineering.py
```

### Warnings sobre entity_key_serialization_version
**Solução**: Já corrigido! Se ainda aparecer, verifique que `feature_store.yaml` tem `entity_key_serialization_version: 3`

## 📈 Benefícios da Integração

### ✅ Implementado
- Separação clara entre entity (student_id) e target (PEDRA)
- Modo híbrido com fallback automático
- Versionamento de features via Parquet
- Consistência de dados entre treinamento e Feast
- Backward compatibility (modo legado funciona)

### 🔜 Possíveis Extensões Futuras
- Online serving para predições em tempo real
- Feature versioning com múltiplas versões de features
- Feature monitoring (drift, quality)
- Integração com prediction service (usar Feast para inferência também)

## 🎓 Conceitos Importantes

### Por que usar student_id em vez de PEDRA?

**PEDRA é o TARGET (y), não um IDENTIFICADOR**:
- ❌ Errado: `Entity(name="pedra", join_keys=["PEDRA"])`
  - PEDRA contém classes: Ametista, Rubi, Safira, etc.
  - São os valores que queremos PREVER
  - Não identificam linhas únicas (múltiplos estudantes podem ter mesma PEDRA)

- ✅ Correto: `Entity(name="student", join_keys=["student_id"])`
  - student_id identifica cada linha/estudante unicamente
  - Permite recuperar features para qualquer estudante
  - PEDRA é armazenado separadamente como target

### Feast Offline vs Online Store

**Offline Store** (usado no treinamento):
- Armazena features históricas
- Usado para criar datasets de treinamento
- Formato: Parquet files
- Acesso: Batch (get_historical_features)

**Online Store** (não usado ainda):
- Armazena features mais recentes
- Usado para predições em tempo real
- Formato: SQLite (neste projeto)
- Acesso: Baixa latência (get_online_features)

## 📚 Referências

- [Documentação Oficial do Feast](https://docs.feast.dev/)
- [Feast Quickstart](https://docs.feast.dev/getting-started/quickstart)
- [Feast Concepts](https://docs.feast.dev/getting-started/concepts)

## ✅ Checklist de Verificação

Após implementação, verifique:

- [x] preprocessing.py adiciona student_id
- [x] feature_engineering.py usa Entity("student")
- [x] FeatureView renomeada para student_features
- [x] train.py suporta --use-feast flag
- [x] training_service.py passa use_feast parameter
- [x] Ambos os modos (Feast e Excel) funcionam
- [x] Sem deprecation warnings do Feast
- [x] Tests passam com ambos os modos

---

**Última Atualização**: 2026-03-07  
**Versão**: 1.0  
**Autor**: AI Assistant  
**Status**: ✅ Produção
