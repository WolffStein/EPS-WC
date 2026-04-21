# Rastreabilidade Tecnica do MVP

## Objetivo deste documento

Este arquivo existe para deixar um rastro tecnico claro sobre:

- o problema de negocio que o projeto esta tentando resolver
- as decisoes de arquitetura tomadas ate aqui
- as hipoteses usadas enquanto o material oficial ainda nao chegou
- a forma como o MVP foi estruturado dentro do repositorio
- o que ja foi implementado
- o que ainda esta pendente

Ele nao representa um "pensamento interno bruto", e sim uma trilha tecnica de decisao.
Ou seja: o foco aqui e registrar contexto, justificativas, impactos e proximos passos de forma
que qualquer pessoa da equipe consiga entrar no projeto e entender por que ele foi montado assim.

---

## 1. Contexto do problema

A necessidade levantada na reuniao com o delegado foi a seguinte:

- chefes de departamento criam operacoes
- cada operacao precisa registrar equipe, local de cumprimento e suspeito alvo
- no dia da apreensao, os agentes precisam registrar os itens apreendidos em campo
- o processo atual usa formulario manual
- existem categorias de objetos com campos diferentes
- ao encerrar a apreensao, deve ser gerado um PDF no formato aceito pelo fluxo atual deles
- os dados tambem precisam permanecer salvos em banco proprio da solucao

Conclusao pratica:

- o maior valor do primeiro MVP nao e IA
- o maior valor imediato e digitalizar o formulario operacional
- o fluxo precisa funcionar em celular
- o sistema precisa ser rapido de usar, simples e adaptavel a categorias diferentes

---

## 2. Leituras iniciais do repositorio

### 2.1 Estado encontrado

Quando o trabalho comecou, o repositorio `EPS-WC` tinha:

- dependencias basicas com Poetry
- Django ja listado no `pyproject.toml`
- pipeline DevSecOps inicial
- um `app.py` simples
- nenhum projeto Django estruturado
- nenhuma modelagem do dominio do problema
- nenhuma interface, migracao ou fluxo funcional do produto

### 2.2 Implicacao tecnica

Isso significou que nao havia uma base de produto pronta para extender.

Na pratica, o caminho mais seguro foi:

1. estruturar o projeto Django do zero dentro do repositorio atual
2. transformar o repositorio de "base de onboarding" em "base do MVP real"
3. preservar as exigencias de seguranca e qualidade que ja estavam no repo

---

## 3. Decisao de produto para o primeiro MVP

### 3.1 O que foi priorizado

Foi priorizado um MVP com foco em operacao real:

- cadastro de operacao
- equipe da operacao
- suspeito e local
- categorias configuraveis
- itens apreendidos com campos variaveis por categoria
- encerramento da operacao
- geracao de PDF
- persistencia em banco

### 3.2 O que ficou propositalmente de fora

Nao foi implementado neste momento:

- OCR
- leitura automatica de foto
- extracao de IMEI por IA
- integracao com APIs externas de IA
- autenticacao complexa por perfil
- permissao granular por departamento
- reproduzir com fidelidade absoluta o layout do PDF oficial

### 3.3 Justificativa

A justificativa foi simples:

- o fluxo de negocio principal ainda nao existia no sistema
- o formulario oficial ainda nao tinha sido enviado
- sem o processo basico funcionando, a camada de IA seria precoce

---

## 4. Decisao de stack

### 4.1 Django como base principal

Django foi mantido porque:

- ja estava previsto nas dependencias do projeto
- acelera modelagem, formularios, admin e migracoes
- permite entregar rapido um fluxo web responsivo
- facilita manter rastreabilidade dos dados no banco

### 4.2 Web mobile-first em vez de app nativo

Embora a demanda final fale em "app", a implementacao inicial ficou como web mobile-first.

Motivos:

- o repositorio e a stack atual estavam em Django, nao em Flutter/React Native
- entregar um PWA ou web responsiva e mais rapido para validar o processo
- isso reduz risco e permite provar valor antes de investir em uma camada nativa

Essa escolha nao impede evolucao posterior para app nativo ou empacotamento.

### 4.3 SQLite e PostgreSQL

Foi adotado um modelo duplo:

- SQLite como fallback de desenvolvimento local rapido
- PostgreSQL via Docker para inspeção relacional e ambiente mais proximo de producao

Motivo:

- SQLite acelera os testes e o bootstrap local
- PostgreSQL permite inspecao no pgAdmin e visao melhor das entidades e relacionamentos

---

## 5. Estruturacao do projeto

### 5.1 Projeto Django

Foi criado o projeto Django em:

- [manage.py](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\manage.py)
- [config/settings.py](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\config\settings.py)
- [config/urls.py](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\config\urls.py)

### 5.2 App de dominio

Foi criado o app principal:

- [apreensoes](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\apreensoes)

Esse app concentra:

- modelos de negocio
- formularios
- views
- administracao
- geracao de PDF
- testes
- migracoes

### 5.3 Camadas criadas

As responsabilidades ficaram separadas assim:

- `models.py`: entidades e regras simples do dominio
- `forms.py`: formularios do Django e montagem dinamica dos campos de categoria
- `views.py`: fluxo de telas e operacoes do usuario
- `pdf.py`: construcao do documento PDF
- `tests.py`: testes do fluxo principal
- `templates/`: interface HTML
- `static/css/app.css`: identidade visual e layout responsivo

---

## 6. Modelagem do dominio

### 6.1 Entidades principais

A modelagem ficou centrada em quatro areas:

1. operacao
2. equipe
3. categoria
4. item apreendido

### 6.2 Modelo `Operation`

Responsavel por representar a operacao policial.

Campos principais:

- codigo
- nome
- departamento
- responsavel
- data da operacao
- horario previsto
- local
- cidade/UF
- suspeito
- documento do suspeito
- endereco do suspeito
- status
- observacoes
- data/hora de encerramento

Estados:

- planejada
- em andamento
- encerrada

### 6.3 Modelo `TeamMember`

Representa os integrantes da equipe ligados a uma operacao.

Campos principais:

- nome
- cargo
- matricula
- contato
- observacoes

Relacionamento:

- varios integrantes pertencem a uma operacao

### 6.4 Modelo `EvidenceCategory`

Representa uma categoria de item apreendido.

Exemplos:

- eletronicos
- veiculos
- documentos
- midias de armazenamento
- outros

Objetivo:

- permitir categorias padrao
- permitir categorias novas criadas no proprio sistema

### 6.5 Modelo `CategoryField`

Representa os campos dinamicos de uma categoria.

Exemplo:

- categoria "Eletronicos" pode ter IMEI, numero de serie, marca, modelo
- categoria "Veiculos" pode ter placa, chassi, renavam, cor

Tipos suportados:

- texto curto
- texto longo
- inteiro
- decimal
- data
- booleano

### 6.6 Modelo `SeizedItem`

Representa cada item apreendido na operacao.

Campos principais:

- operacao
- categoria
- titulo
- quantidade
- descricao
- local encontrado
- estado
- `extra_data` em JSON para os campos especificos da categoria

### 6.7 Decisao importante de modelagem

O uso de `extra_data` em JSON foi intencional.

Motivo:

- evita explodir o banco com muitas colunas opcionais
- permite adicionar novas categorias sem alterar o schema a cada vez
- combina bem com o requisito de formularios dinamicos

Trade-off:

- parte dos dados fica menos normalizada
- em troca, o sistema ganha flexibilidade para o MVP

---

## 7. Categorias padrao semeadas

Foi criada uma migracao de seed:

- [apreensoes/migrations/0002_seed_default_categories.py](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\apreensoes\migrations\0002_seed_default_categories.py)

Ela insere categorias iniciais com campos que fazem sentido para o dominio:

- Eletronicos
- Veiculos
- Documentos
- Midias de armazenamento
- Outros

Justificativa:

- o usuario nao comeca com o sistema vazio
- o time ganha um ponto de partida realista
- reduz friccao na demonstracao do MVP

---

## 8. Formularios dinamicos

### 8.1 Problema

Itens apreendidos nao compartilham sempre os mesmos campos.

### 8.2 Solucao implementada

O formulario de item:

- sempre tem campos base
- carrega campos extras conforme a categoria escolhida
- salva os valores extras em `extra_data`

Arquivo principal:

- [apreensoes/forms.py](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\apreensoes\forms.py)

### 8.3 Beneficio

Isso entrega a adaptabilidade exigida pelo processo sem travar a equipe em uma unica estrutura de formulario.

---

## 9. Fluxo de interface

### 9.1 Tela inicial

A home mostra:

- operacoes existentes
- contadores por status
- acesso rapido para criar nova operacao

Arquivo:

- [templates/apreensoes/dashboard.html](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\templates\apreensoes\dashboard.html)

### 9.2 Detalhe da operacao

Na tela da operacao, o usuario consegue:

- ver dados da diligencia
- iniciar a operacao
- encerrar a operacao
- adicionar equipe
- registrar itens
- baixar PDF

Arquivo:

- [templates/apreensoes/operation_detail.html](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\templates\apreensoes\operation_detail.html)

### 9.3 Tela de categorias

Permite:

- listar categorias
- criar nova categoria
- adicionar campos especificos

### 9.4 Decisao visual

Foi adotada uma interface web mobile-first com:

- botoes grandes
- cards
- navegacao simples
- layout responsivo

Arquivo de estilo:

- [static/css/app.css](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\static\css\app.css)

---

## 10. Geracao de PDF

### 10.1 Estado atual

O projeto gera PDF funcional com:

- dados da operacao
- equipe
- itens apreendidos
- detalhes extras por categoria

Arquivo:

- [apreensoes/pdf.py](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\apreensoes\pdf.py)

### 10.2 Biblioteca escolhida

Foi usado `reportlab`.

Motivos:

- controle direto da composicao do documento
- integracao simples com Django
- geracao server-side estavel

### 10.3 Limitacao conhecida

O layout ainda nao replica o formulario oficial da PCDF com fidelidade total.

Motivo:

- o PDF base ainda nao foi recebido

Plano:

- quando o PDF oficial chegar, ajustar o layout e a distribuicao visual do documento

---

## 11. Docker, PostgreSQL e pgAdmin

### 11.1 Problema resolvido

Era necessario inspecionar visualmente o banco e os relacionamentos.

### 11.2 Solucao implementada

Foi criado um ambiente Docker com:

- `web`: aplicacao Django
- `db`: PostgreSQL
- `pgadmin`: inspecao visual do banco

Arquivo:

- [docker-compose.yml](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\docker-compose.yml)

### 11.3 Configuracao do Django

O `settings.py` agora:

- usa SQLite por padrao fora do Docker
- usa PostgreSQL quando `DB_ENGINE=postgres`

### 11.4 pgAdmin preconfigurado

Foi adicionado:

- [pgadmin/servers.json](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\pgadmin\servers.json)

Objetivo:

- deixar o servidor ja cadastrado
- acelerar a inspecao das tabelas
- facilitar uso do ERD Tool

---

## 12. Preocupacoes de seguranca e qualidade

As mudancas foram validadas com:

- `python manage.py check`
- `python manage.py test`
- `ruff check .`
- `bandit -r .`
- `docker compose config`

Decisoes relevantes:

- `SECRET_KEY` nao ficou hardcoded fixa de producao
- o banco pode ser configurado por variavel de ambiente
- o compose separa responsabilidades por servico
- o pgAdmin ficou em modo pratico para ambiente de desenvolvimento

---

## 13. Hipoteses assumidas ate aqui

Como parte do material de negocio ainda nao chegou, algumas hipoteses foram necessarias:

### 13.1 Hipotese sobre o PDF

Hipotese:

- o conteudo do PDF importa mais que o layout exato neste primeiro momento

Impacto:

- permitiu construir a logica sem bloquear a entrega

### 13.2 Hipotese sobre o uso em campo

Hipotese:

- uma interface web responsiva ja e suficiente para validacao operacional inicial

Impacto:

- entregamos valor mais rapido

### 13.3 Hipotese sobre categorias

Hipotese:

- categorias padrao ajudam, mas o sistema precisa permitir extensao

Impacto:

- a modelagem foi desenhada para flexibilidade

---

## 14. O que ja esta pronto para demonstracao

Hoje o sistema ja permite demonstrar:

1. criar operacao
2. cadastrar equipe
3. listar categorias
4. criar categoria nova
5. criar campos para categoria
6. registrar item apreendido com campos especificos
7. iniciar e encerrar operacao
8. gerar PDF
9. inspecionar estrutura relacional no PostgreSQL via pgAdmin

---

## 15. Pendencias e proximos passos recomendados

### 15.1 Alta prioridade

- receber o formulario/PDF oficial da PCDF
- ajustar o layout do PDF para aderencia visual exata
- criar usuario admin inicial e fluxo simples de acesso
- definir quais campos sao obrigatorios por operacao real

### 15.2 Media prioridade

- melhorar rastreabilidade de alteracoes nos itens
- incluir upload de imagens por item apreendido
- registrar cadeia de custodia basica
- adicionar busca e filtros nas operacoes

### 15.3 Evolucao futura com IA

Depois do fluxo base consolidado:

- OCR de serial e IMEI
- leitura assistida por foto
- preenchimento semi-automatico do formulario
- revisao humana obrigatoria antes do fechamento

---

## 16. Estrutura atual do projeto

Mapa resumido do que existe hoje:

- [config](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\config): configuracao Django
- [apreensoes](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\apreensoes): dominio principal da aplicacao
- [templates](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\templates): interface HTML
- [static](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\static): estilos da aplicacao
- [pgadmin](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\pgadmin): configuracao do pgAdmin
- [docker-compose.yml](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\docker-compose.yml): ambiente containerizado
- [README.md](C:\Users\Cliente\Documents\FGA2\EPS\EPS-WC\README.md): instrucoes de uso

---

## 17. Resumo executivo

O projeto saiu de um repositorio base de onboarding e passou a ser um MVP funcional de apoio a
apreensoes. A estrutura atual foi pensada para entregar valor rapido no processo de negocio,
mantendo flexibilidade para:

- adaptar categorias
- gerar PDF
- trocar banco
- evoluir para IA depois

Em outras palavras:

- primeiro foi garantido o processo operacional
- depois foi garantida a persistencia
- depois a exportacao em PDF
- depois a inspecao relacional com PostgreSQL e pgAdmin

Esse encadeamento foi a espinha dorsal da estruturacao do projeto ate aqui.
