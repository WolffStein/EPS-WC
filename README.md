# EPS-WC

Repositorio base do desafio de onboarding SecOps + configuracao Git.

## Objetivo deste repositorio

Este repositorio foi preparado para atender os requisitos tecnicos da Fase 1:

- gerenciamento de dependencias com Poetry
- base Django 5+
- esteira DevSecOps com SAST, SCA, qualidade e secret scanning
- relatorio de prontidao tecnica em Markdown

## Setup local

1. Instale Python 3.12
2. Instale Poetry
3. No repositorio, execute:

```bash
poetry config virtualenvs.in-project true
poetry install
```

## Comandos de verificacao

```bash
poetry env info
poetry run bandit -r . --exclude ./.venv,./.git,./.github,./.ruff_cache
poetry run ruff check .
poetry run safety scan
```

## CI de seguranca

A pipeline esta em `.github/workflows/devsecops.yml` e executa:

- Ruff
- Bandit
- Safety
- Gitleaks (secret scanning)

## Relatorio de prontidao

O relatorio solicitado no desafio esta em:

- `desafio1/relatorio_prontidao.md`