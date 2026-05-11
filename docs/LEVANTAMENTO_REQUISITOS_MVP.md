# Levantamento de Requisitos do MVP

## 1. Objetivo do documento

Este documento formaliza o levantamento inicial de requisitos do projeto `EPS-WC`, com foco no
MVP de apoio a operacoes de apreensao.

O objetivo aqui e:

- registrar o problema de negocio que o produto resolve
- identificar atores e necessidades principais
- definir o escopo do MVP
- consolidar requisitos funcionais, nao funcionais e regras de negocio
- destacar hipoteses e pontos que ainda precisam de validacao com o cliente

Este levantamento foi construido a partir:

- das anotacoes da reuniao com o delegado
- do fluxo implementado no MVP atual
- da rastreabilidade tecnica do projeto

---

## 2. Contexto do problema

Hoje, o processo de apreensao depende de formularios manuais preenchidos pelos agentes durante ou
apos a operacao.

O problema identificado e:

- o registro manual torna o processo mais lento
- os itens apreendidos podem pertencer a categorias muito diferentes
- cada categoria pode exigir campos especificos
- ao final da operacao, os dados precisam ser organizados em um PDF compativel com o fluxo atual
- os registros tambem precisam permanecer armazenados em banco proprio da solucao

O valor principal do MVP e digitalizar o inventario operacional de apreensao, mantendo o uso simples
em celular e criando base para futuras automacoes com IA.

---

## 3. Objetivo do produto

Disponibilizar uma aplicacao web mobile-first que permita:

- cadastrar operacoes de apreensao
- organizar equipe, local e suspeito alvo
- registrar itens apreendidos com formularios dinamicos por categoria
- anexar imagens dos itens
- gerar sugestoes de preenchimento com apoio de IA
- revisar manualmente os dados
- gerar um PDF final da operacao
- manter os dados persistidos em banco

---

## 4. Escopo do MVP

### 4.1 Incluido no MVP

- cadastro e edicao de operacoes
- controle basico de status da operacao
- cadastro de integrantes da equipe
- cadastro e manutencao de categorias de itens
- definicao de campos dinamicos por categoria
- registro de itens apreendidos
- upload de imagem por item
- analise assistida por IA a partir da imagem
- preenchimento automatico assistido com revisao humana
- autenticacao simples com usuario e senha
- geracao de PDF funcional
- persistencia em banco SQLite ou PostgreSQL
- interface web responsiva para uso em celular

### 4.2 Fora do escopo atual

- controle granular por perfis e permissoes detalhadas
- integracao direta com o sistema oficial externo
- envio automatico do PDF ao sistema oficial
- OCR especializado para serial, IMEI, chassi ou placa
- uso offline
- cadeia de custodia completa
- trilha detalhada de auditoria por usuario
- app nativo para Android/iOS
- fidelidade visual total ao PDF oficial ainda nao recebido

---

## 5. Stakeholders e atores

### 5.1 Stakeholders principais

- delegado / cliente de negocio
- chefes de departamento
- agentes em campo
- equipe de desenvolvimento
- professor / orientacao academica

### 5.2 Atores do sistema

#### A1. Chefe de departamento

Responsavel por criar e estruturar a operacao.

Necessidades:

- registrar dados gerais da operacao
- montar a equipe
- definir o alvo e o local
- acompanhar os itens registrados
- encerrar a operacao e gerar PDF

#### A2. Agente em campo

Responsavel por registrar os itens apreendidos durante a diligencia.

Necessidades:

- usar o sistema pelo celular
- registrar itens com rapidez
- anexar imagens
- obter apoio da IA sem perder o controle manual do preenchimento

#### A3. Administrador / equipe interna

Responsavel por apoiar manutencao operacional e tecnica.

Necessidades:

- consultar registros
- validar estrutura de dados
- administrar categorias
- inspecionar banco e modelo relacional

---

## 6. Fluxo de negocio esperado

### 6.1 Fluxo principal

1. O chefe cria uma operacao.
2. O chefe registra equipe, local e suspeito alvo.
3. A operacao fica pronta para uso em campo.
4. Durante a apreensao, os agentes registram os itens.
5. Para cada item, o agente escolhe a categoria e preenche os campos necessarios.
6. Quando houver foto, o agente anexa a imagem.
7. O sistema pode usar IA para sugerir preenchimento.
8. O agente revisa manualmente as sugestoes.
9. Ao final, a operacao e encerrada.
10. O sistema gera um PDF consolidado da operacao.
11. O PDF e usado no fluxo oficial externo.

### 6.2 Fluxo de apoio com IA

1. O agente registra o item e envia uma imagem.
2. O sistema chama um provider de IA visual.
3. A IA devolve sugestoes estruturadas.
4. O sistema exibe sugestoes e avisos de revisao.
5. O agente decide se aplica ou nao o preenchimento automatico.
6. Em cenas mistas, o sistema recomenda criar registros separados.

---

## 7. Requisitos funcionais

### 7.1 Operacoes

- `RF01` O sistema deve permitir cadastrar uma operacao de apreensao.
- `RF02` O sistema deve permitir editar uma operacao enquanto ela nao estiver encerrada.
- `RF03` O sistema deve permitir consultar a lista de operacoes cadastradas.
- `RF04` O sistema deve permitir visualizar o detalhe de uma operacao.
- `RF05` O sistema deve permitir iniciar uma operacao planejada.
- `RF06` O sistema deve permitir encerrar uma operacao.
- `RF07` O sistema deve impedir alteracoes em operacoes encerradas.

### 7.2 Equipe

- `RF08` O sistema deve permitir adicionar integrantes a uma operacao.
- `RF09` O sistema deve permitir remover integrantes de uma operacao enquanto ela nao estiver encerrada.
- `RF10` O sistema deve exibir a equipe associada a cada operacao.

### 7.3 Categorias e campos dinamicos

- `RF11` O sistema deve disponibilizar categorias padrao para o inicio do uso.
- `RF12` O sistema deve permitir criar novas categorias de itens apreendidos.
- `RF13` O sistema deve permitir visualizar os detalhes de uma categoria.
- `RF14` O sistema deve permitir adicionar campos dinamicos a uma categoria.
- `RF15` O sistema deve permitir marcar campos de categoria como obrigatorios ou opcionais.
- `RF16` O sistema deve exibir no formulario de item os campos dinamicos da categoria selecionada.

### 7.4 Itens apreendidos

- `RF17` O sistema deve permitir registrar um item apreendido vinculado a uma operacao.
- `RF18` O sistema deve permitir editar um item apreendido enquanto a operacao nao estiver encerrada.
- `RF19` O sistema deve permitir remover um item apreendido enquanto a operacao nao estiver encerrada.
- `RF20` O sistema deve permitir informar categoria, titulo, quantidade, descricao, local encontrado e estado do item.
- `RF21` O sistema deve permitir armazenar valores adicionais em campos dinamicos da categoria.
- `RF22` O sistema deve permitir anexar uma imagem ao item apreendido.
- `RF23` O sistema deve exibir os itens registrados dentro da operacao.

### 7.5 IA assistida por imagem

- `RF24` O sistema deve permitir solicitar analise de imagem para um item com foto anexada.
- `RF25` O sistema deve armazenar a resposta estruturada retornada pela IA.
- `RF26` O sistema deve exibir titulo sugerido, categoria sugerida, atributos visiveis, observacoes e faltas identificadas pela IA.
- `RF27` O sistema deve permitir aplicar automaticamente sugestoes da IA no item.
- `RF28` O sistema deve manter a revisao humana como etapa obrigatoria do processo.
- `RF29` O sistema deve sinalizar quando a imagem aparentar conter mais de um registro potencial.
- `RF30` O sistema deve listar grupos detectados em cenas mistas para orientar desmembramento manual.

### 7.6 PDF e saida operacional

- `RF31` O sistema deve permitir gerar um PDF com os dados consolidados da operacao.
- `RF32` O PDF deve conter os dados da operacao, equipe e itens apreendidos.
- `RF33` O PDF deve ser disponibilizado para download.

### 7.7 Administracao e apoio

- `RF34` O sistema deve disponibilizar area administrativa do Django para apoio operacional.
- `RF35` O sistema deve permitir inspecao do banco relacional via PostgreSQL e pgAdmin no ambiente local de desenvolvimento.

### 7.8 Autenticacao e acesso

- `RF36` O sistema deve permitir que usuarios autenticados entrem com usuario e senha.
- `RF37` O sistema deve permitir encerramento de sessao pelo usuario autenticado.
- `RF38` O sistema deve restringir o acesso as telas principais do produto a usuarios autenticados.

---

## 8. Regras de negocio

- `RN01` Toda operacao deve possuir um codigo unico.
- `RN02` Toda operacao inicia com status `planejada`.
- `RN03` Uma operacao planejada pode ser movida para `em andamento`.
- `RN04` Uma operacao encerrada nao pode ser editada nem receber novos itens ou integrantes.
- `RN05` Todo item apreendido deve pertencer a uma operacao.
- `RN06` Todo item apreendido deve pertencer a uma categoria.
- `RN07` A quantidade de um item deve ser maior ou igual a 1.
- `RN08` Cada categoria deve possuir `slug` unico.
- `RN09` Cada campo dinamico deve possuir chave unica dentro da sua categoria.
- `RN10` O preenchimento por IA deve ser assistido e revisavel, nunca definitivo por si so.
- `RN11` Em imagens com mais de um grupo de evidencia, o sistema deve priorizar comportamento conservador.
- `RN12` O sistema nao deve inventar atributos nao sustentados visualmente pela imagem.
- `RN13` O PDF deve ser gerado apenas com base nos dados persistidos da operacao.

---

## 9. Requisitos nao funcionais

### 9.1 Usabilidade

- `RNF01` A interface deve ser pensada para uso em celular.
- `RNF02` O fluxo de registro deve exigir o minimo possivel de navegacao em campo.
- `RNF03` O sistema deve apresentar formularios claros e adaptados por categoria.

### 9.2 Desempenho

- `RNF04` O carregamento das telas principais deve ser adequado ao uso operacional cotidiano.
- `RNF05` A geracao do PDF deve ocorrer em tempo compativel com encerramento da operacao.

### 9.3 Confiabilidade e persistencia

- `RNF06` Os dados registrados devem permanecer persistidos em banco proprio da solucao.
- `RNF07` O sistema deve continuar funcional sem dependencia obrigatoria da IA para o fluxo base.

### 9.4 Seguranca

- `RNF08` Chaves de API externas nao devem ser expostas no frontend.
- `RNF09` O uso de IA deve ocorrer pelo backend.
- `RNF10` O sistema deve permitir configuracao por variaveis de ambiente.

### 9.5 Manutenibilidade

- `RNF11` O projeto deve manter estrutura organizada em camadas de dominio, formularios, views, templates e testes.
- `RNF12` O projeto deve possuir cobertura minima de testes do fluxo principal do MVP.

### 9.6 Portabilidade e ambiente

- `RNF13` O sistema deve rodar localmente com SQLite para desenvolvimento rapido.
- `RNF14` O sistema deve rodar com PostgreSQL em ambiente Docker.
- `RNF15` O ambiente local deve permitir inspecao do banco via pgAdmin.

---

## 10. Requisitos de dados

### 10.1 Dados da operacao

O sistema deve armazenar, no minimo:

- codigo
- nome
- departamento
- responsavel
- data da operacao
- horario previsto
- local da apreensao
- cidade/UF
- suspeito nome
- suspeito documento
- suspeito endereco
- status
- observacoes
- data/hora de encerramento

### 10.2 Dados da equipe

O sistema deve armazenar, no minimo:

- nome
- cargo
- matricula
- contato
- observacoes

### 10.3 Dados do item apreendido

O sistema deve armazenar, no minimo:

- categoria
- titulo
- quantidade
- descricao
- local encontrado
- estado
- imagem anexada
- dados dinamicos por categoria
- dados de analise de IA quando houver

---

## 11. Priorizacao inicial

### 11.1 Alta prioridade

- cadastro de operacao
- cadastro de equipe
- registro de item
- categorias dinamicas
- geracao de PDF
- persistencia em banco
- uso via celular

### 11.2 Media prioridade

- upload de imagem
- apoio da IA ao preenchimento
- separacao de cenas mistas
- ajuda contextual na interface

### 11.3 Baixa prioridade para o MVP atual

- OCR especializado
- integracao automatica com sistema externo
- controle avancado por perfil e permissao
- cadeia de custodia detalhada
- app nativo

---

## 12. Hipoteses assumidas

As seguintes hipoteses foram assumidas ate o momento:

- o maior valor inicial esta no inventario digital, nao na IA
- uma interface web responsiva e suficiente para validar o processo em campo
- o PDF funcional ja agrega valor mesmo antes do modelo oficial final
- as categorias precisam ser extensiveis para cobrir tipos diferentes de apreensao
- a IA deve atuar como assistente conservadora, e nao como automacao cega

---

## 13. Pontos pendentes de validacao com o cliente

Os itens abaixo ainda precisam ser confirmados formalmente:

- layout exato do PDF oficial
- campos obrigatorios por tipo real de operacao
- necessidade de perfis de acesso diferentes por papel operacional
- necessidade futura de uso offline
- politica de retencao e sigilo das imagens
- integracao futura com sistema oficial externo
- nivel de aceitacao do uso de IA com dados sensiveis
- necessidade de trilha de auditoria por usuario
- padronizacao definitiva das categorias default

---

## 14. Riscos identificados

- ausencia do PDF oficial pode gerar retrabalho de layout
- ausencia de definicao de perfis pode impactar seguranca na fase seguinte
- dependencia de IA externa pode ser sensivel para dados policiais
- cenas mistas podem induzir preenchimento incorreto se o comportamento nao for conservador
- crescimento descontrolado de categorias pode exigir governanca futura

---

## 15. Criterio de aceite do MVP

O MVP pode ser considerado apto para demonstracao quando:

- for possivel criar uma operacao completa
- for possivel cadastrar equipe
- for possivel registrar itens com categorias dinamicas
- for possivel anexar imagens
- for possivel obter sugestoes assistidas por IA
- for possivel revisar manualmente os dados
- for possivel encerrar a operacao
- for possivel gerar e baixar o PDF
- os dados permanecerem persistidos no banco

---

## 16. Relacao com a implementacao atual

Este levantamento ja possui aderencia direta ao que esta implementado hoje no projeto, especialmente
nos seguintes pontos:

- operacoes, equipe, categorias, campos dinamicos e itens ja existem no dominio
- a interface web mobile-first ja foi iniciada
- a persistencia em banco ja esta pronta
- a geracao de PDF ja esta funcional
- a analise assistida por IA ja foi integrada como apoio ao preenchimento

Ou seja: este documento registra os requisitos do MVP e ao mesmo tempo ajuda a alinhar o que ja foi
entregue com o que ainda precisa ser validado ou evoluido.
