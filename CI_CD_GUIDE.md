# 🔄 CI/CD com GitHub Actions

Este projeto usa GitHub Actions para automação de testes, lint e build Docker.

## 📝 Configuração

O workflow está em [.github/workflows/ci.yml](.github/workflows/ci.yml) e executa automaticamente em:
- **Push** para branches `main`, `master` ou `develop`
- **Pull Requests** para essas mesmas branches

## 🎯 Jobs Configurados

### 1. **Test** 
- Instala dependências Python
- Roda testes unitários com pytest
- Gera relatório de cobertura
- Upload opcional para Codecov

### 2. **Lint**
- Verifica erros críticos com flake8
- Analisa qualidade de código
- Executa em paralelo com os testes

### 3. **Docker**
- Executa apenas após testes passarem
- Apenas em push para `main`/`master`
- Builda imagem Docker
- Testa inicialização do container
- Verifica health endpoint

## 🚀 Como Usar

### Primeira vez (configuração no GitHub)

1. **Fazer push do código:**
```bash
git add .
git commit -m "Adiciona CI/CD com GitHub Actions"
git push origin main
```

2. **Verificar execução:**
   - Vá para seu repositório no GitHub
   - Clique na aba **Actions**
   - Veja os workflows rodando

3. **Atualizar badge do README:**
   - Substitua `USERNAME` pelo seu usuário do GitHub no [README.md](README.md):
   ```markdown
   [![CI/CD Pipeline](https://github.com/SEU-USUARIO/dt-2/actions/workflows/ci.yml/badge.svg)](https://github.com/SEU-USUARIO/dt-2/actions/workflows/ci.yml)
   ```

### Execução automática

Após configurado, o CI/CD roda automaticamente em:
- Cada commit para `main`, `master` ou `develop`
- Cada Pull Request criado
- Você pode re-rodar manualmente no GitHub Actions

## ✅ Status dos Testes

Você pode verificar o status atual clicando no badge no README:

[![CI/CD Pipeline](https://github.com/USERNAME/dt-2/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/dt-2/actions/workflows/ci.yml)

**Status possíveis:**
- 🟢 **Passing** - Todos os testes passaram
- 🔴 **Failing** - Algum teste falhou
- 🟡 **Running** - Workflow em execução

## 🔧 Comandos Úteis

### Rodar testes localmente (como no CI)

```bash
# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=app --cov=src --cov-report=term-missing

# Apenas unitários (mais rápido)
pytest tests/test_preprocessing.py tests/test_model.py -v
```

### Lint local

```bash
# Instalar flake8
pip install flake8

# Verificar erros críticos
flake8 app/ src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics

# Análise completa
flake8 app/ src/ tests/ --count --max-complexity=10 --max-line-length=127 --statistics
```

### Testar build Docker local

```bash
# Build
docker-compose build --no-cache

# Iniciar
docker-compose up -d

# Testar health
curl http://localhost:8000/health

# Parar
docker-compose down
```

## 📊 Cobertura de Código

O workflow gera relatórios de cobertura automaticamente. Para integrar com Codecov:

1. Crie conta em [codecov.io](https://codecov.io)
2. Adicione seu repositório
3. O token é configurado automaticamente para repos públicos

## 🐛 Troubleshooting

### Testes falhando no CI mas passando localmente

**Causa comum:** Modelos ou dados faltando no repositório
**Solução:** 
- Certifique-se que `src/bases/dados_pedras_baixo_erro.xlsx` está no Git
- Testes da API podem falhar se `app/modelo` estiver vazio (é esperado)

### Docker build falhando

**Causa comum:** Falta de recursos ou timeout
**Solução:**
- Use cache do Docker: já configurado no workflow
- Build pode demorar 3-5 minutos na primeira vez

### Python version not found

**Erro:** `Version 3.14 with arch x64 not found`
**Solução:** Python 3.14 configurado no workflow

## 📚 Recursos

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pytest Documentation](https://docs.pytest.org)
- [Flake8 Documentation](https://flake8.pycqa.org)
- [Codecov Documentation](https://docs.codecov.com)

## 🔒 Secrets (Opcional)

Para configurações avançadas, você pode adicionar secrets no GitHub:

1. Vá em **Settings** > **Secrets and variables** > **Actions**
2. Clique em **New repository secret**
3. Adicione secrets como:
   - `CODECOV_TOKEN` (se repo privado)
   - `DOCKER_USERNAME` (para push de imagens)
   - `DOCKER_PASSWORD`

---

**Nota:** O workflow está configurado para falhar gracefully se algum serviço opcional (como Codecov) não estiver disponível.
