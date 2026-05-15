# EPS-WC

MVP mobile-first para apoio a operacoes de apreensao da PCDF.

## O que ja foi implementado

- cadastro de operacoes com departamento, chefe responsavel, local e suspeito
- gestao da equipe da operacao
- catalogo de categorias configuraveis com campos dinamicos
- categorias padrao semeadas automaticamente:
  - eletronicos
  - veiculos
  - documentos
  - midias de armazenamento
  - armas
  - drogas
  - outros
- registro de itens apreendidos com formulario adaptavel por categoria
- upload de imagem por item apreendido
- analise assistida por IA com Gemini para sugerir preenchimento a partir da foto
- foco inicial de teste visual em armas e drogas com preenchimento automatico assistido
- login para acesso as telas do sistema
- persistencia em banco SQLite ou PostgreSQL
- encerramento da operacao com geracao de PDF
- interface web responsiva pensada para uso em celular
- base Android em `android-apk/` para empacotamento em APK via WebView
- area administrativa do Django em `/admin/`
- ambiente Docker com PostgreSQL e pgAdmin para inspecao do modelo relacional

## Stack

- Python 3.12+
- Django 5
- ReportLab para geracao de PDF
- Google Gen AI SDK para analise estruturada de imagens
- SQLite para desenvolvimento local rapido
- PostgreSQL + pgAdmin para inspecao da estrutura relacional via Docker

## Documentacao de contexto

Para entender a linha de estruturacao do MVP, as decisoes de arquitetura e o estado atual do
projeto, consulte:

- [docs/RASTREABILIDADE_TECNICA_MVP.md](docs/RASTREABILIDADE_TECNICA_MVP.md)
- [docs/LEVANTAMENTO_REQUISITOS_MVP.md](docs/LEVANTAMENTO_REQUISITOS_MVP.md)
- [docs/APK_ANDROID.md](docs/APK_ANDROID.md)

## Como rodar localmente

1. Instale as dependencias:

```bash
poetry install
```

2. Rode as migracoes:

```bash
poetry run python manage.py migrate
```

3. Crie um usuario para entrar no sistema:

```bash
poetry run python manage.py createsuperuser
```

4. Suba o servidor:

```bash
poetry run python manage.py runserver
```

5. Acesse:

- aplicacao: `http://127.0.0.1:8000/`
- admin: `http://127.0.0.1:8000/admin/`

6. Para testar a analise de imagem com IA:

- preencha `GEMINI_API_KEY` no arquivo `.env`
- opcionalmente ajuste `GEMINI_VISION_MODEL` se quiser trocar o modelo

## Como subir com Docker + PostgreSQL + pgAdmin

```bash
docker compose up --build
```

Servicos disponiveis:

- aplicacao Django: `http://127.0.0.1:8000/`
- pgAdmin: `http://127.0.0.1:5050/`
- PostgreSQL: `localhost:5432`

Credenciais padrao do pgAdmin:

- email: `admin@eps.local`
- senha: `admin123`

Credenciais padrao do PostgreSQL:

- banco: `eps_db`
- usuario: `eps_user`
- senha: `eps_password`

Variaveis de IA disponiveis no ambiente Docker:

- `GEMINI_API_KEY`
- `GEMINI_VISION_MODEL` (padrao: `gemini-2.5-flash`)

O arquivo `pgadmin/servers.json` deixa o servidor `EPS PostgreSQL` pre-cadastrado no pgAdmin.
Ao abrir o servidor pela primeira vez, use a senha do PostgreSQL para conectar. Depois disso,
voce ja consegue navegar nas tabelas e usar `Tools > ERD Tool` para inspecionar os
relacionamentos entre as entidades.

## Fluxo do MVP

1. Criar a operacao.
2. Cadastrar a equipe.
3. Conferir ou ajustar categorias.
4. Lancar os itens apreendidos e anexar imagem quando houver.
5. Pedir apoio da IA para sugerir preenchimento com base na foto, com foco inicial em armas e drogas.
6. Revisar manualmente os dados sugeridos.
7. Encerrar a operacao.
8. Baixar o PDF gerado para posterior envio ao sistema oficial.

## Testes e verificacoes

```bash
poetry run python manage.py test
poetry run python manage.py check
poetry run ruff check .
poetry run bandit -r . --exclude ./.venv,./.git,./.github,./.ruff_cache
```

## Observacao importante

O PDF ja e gerado a partir dos dados da operacao, mas o layout ainda esta preparado como
template funcional do MVP. Assim que o formulario oficial da PCDF for enviado, o arquivo pode
ser ajustado para reproduzir o modelo visual exato. A IA tambem esta na fase de assistencia:
ela sugere preenchimento visual, mas a revisao humana continua obrigatoria.

No fluxo atual, a integracao de IA esta preparada para Gemini API. Para prototipacao, o free
tier ajuda bastante, mas a propria documentacao do Google informa que, nesse nivel gratuito,
o conteudo pode ser usado para melhorar os produtos deles. Para dados sensiveis em ambiente
real, vale considerar uma alternativa local como Ollama no futuro.
