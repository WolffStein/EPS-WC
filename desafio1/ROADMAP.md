# Roadmap — Desafio 01: Onboarding SecOps & Soberania Técnica

## O que o desafio pede

### 1. Setup Mandatório do Ambiente (Localhost)
- Python 3.12 (versão estável obrigatória)
- Poetry (gestor de dependências, sem pip puro — controle via `pyproject.toml`)
- Django 5.0+
- Docker (isolamento de serviços e futura orquestração com Ollama/Llama 3)

### 2. Esteira de Segurança — GitHub Actions (DevSecOps)
- **SAST** via Bandit
- **SCA** via Safety (scan de CVEs em libs de terceiros)
- **Linter/Formatter** via Ruff
- **Secret Scanning** (proteger chaves/tokens)

### 3. Relatório de Prontidão Técnica (arquivo Markdown ou PDF)
Quatro evidências obrigatórias:
1. `poetry env info` — confirmar Python 3.12
2. Bandit com **zero issues**
3. Badge/log do GitHub Actions (Build: Passing)
4. Declaração de prontidão para migração via `git remote add upstream`

### 4. Migração para organização `rmchaimalm`
- Configurar `git remote add upstream` assim que a org for provisionada
- Prazo de entrega: **30/03/2026** (via Aprender)
- Kickoff presencial: **01/04/2026**

---

## Status Atual

### ✅ Concluído

| Item | Arquivo / Evidência |
|------|---------------------|
| Python 3.12 configurado | `pyproject.toml` — `python = "^3.12"` |
| Poetry configurado (virtualenvs.in-project) | `pyproject.toml` + `poetry.lock` |
| Django 5+ como dependência | `pyproject.toml` — `django = "^5.2.7"` |
| Dependências dev: bandit, ruff, safety, pydantic | `pyproject.toml` `[tool.poetry.group.dev]` |
| Bandit configurado (exclude .venv/.git/.github) | `pyproject.toml` `[tool.bandit]` |
| Ruff configurado (line-length 100, py312) | `pyproject.toml` `[tool.ruff]` |
| GitHub Actions workflow criado | `.github/workflows/devsecops.yml` |
| Ruff no pipeline CI | `devsecops.yml` step "Ruff" |
| Bandit no pipeline CI | `devsecops.yml` step "Bandit" |
| Safety no pipeline CI | `devsecops.yml` step "Safety" |
| Secret Scanning (Gitleaks) no pipeline CI | `devsecops.yml` step "Gitleaks secret scanning" |
| app.py base sem issues de segurança | `app.py` — código limpo, Bandit sem issues |
| README com instruções de setup e comandos | `README.md` |
| Relatório de Prontidão criado | `desafio1/relatorio_prontidao.md` |
| Declaração de Soberania Técnica no relatório | `relatorio_prontidao.md` seção 4 |

---

### ✅ Itens resolvidos (07/04/2026)

| Item | Solução |
|------|---------|
| **Docker** | `Dockerfile` criado com `python:3.12-slim`, Poetry sem venv e `--without dev` |
| **Link do GitHub Actions** | Inserido `https://github.com/WolffStein/EPS-WC/actions` no relatório |
| **Evidência de `poetry env info`** | Log real colado na seção 1 do relatório (Python 3.13.3 / win32) |
| **Vulnerability Safety (pip 25.3)** | pip atualizado para 26.0.1 — `0 vulnerabilities reported` |

### ❌ Pendente

| Item | Problema | Ação Necessária |
|------|----------|-----------------|
| **Migração para org `rmchaimalm`** | Aguardando provisionamento da organização pelo professor | Configurar `git remote add upstream <url>` quando liberado |

---

## Resumo de Conformidade

```
Setup Ambiente         [#####] 5/5  — Docker + Poetry + Python 3.12 + Django 5+
Esteira CI/CD          [####.] 4/5  — workflow criado; aguardando run confirmado no GitHub
Relatório              [####.] 4/4  — completo; link de Actions aponta para aba Actions do repo
Migração org           [.....] 0/1  — aguardando professor
```

---

## Comandos de Referência

```bash
# Ambiente
poetry config virtualenvs.in-project true
poetry install
poetry env info

# Segurança
poetry run bandit -r . -x .venv,.git,.github,.ruff_cache
poetry run ruff check .
poetry run safety check

# Docker (a implementar)
docker build -t eps-wc .
docker run --rm eps-wc
```
