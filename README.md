# dev-flow

Marketplace de plugins do Claude Code com o fluxo de desenvolvimento do time: **da demanda explicada em texto até o PR e a pipeline**, passando por especificação funcional, técnica, plano, implementação tarefa a tarefa, revisão e validação — com portões de aprovação humana e proteções que não dependem da memória do modelo.

Nasceu da forma de trabalho do PBI 1001 (Acme.API.Ponte), extraída para servir a qualquer projeto: back-end, front-end, scripts SQL ou vários repositórios na mesma demanda.

```
demanda (você explica)
  → /fluxo:demanda  → 01-funcional.md                ◆ você aprova
  → /fluxo:tecnica  → 02-tecnica.md (código real)    ◆ você aprova
  → /fluxo:plano    → tarefas.json + 03-plano.md      ◆ você aprova  (+ cards no Boards, opcional)
  → /fluxo:task todas → por tarefa: implementa → testa → revisor → validador → commit → feito
  → /fluxo:pr       → pr.md (+ PR aberto depois do seu push)
  → azure-pipelines → CI verde; deploy em produção com aprovação no environment
/fluxo:entregar faz tudo isso em sequência, parando só nos ◆.
```

## Plugins

| Plugin | O que traz |
| --- | --- |
| **fluxo** (núcleo) | Skills `iniciar`, `demanda`, `tecnica`, `plano`, `task`, `entregar`, `pr`, `status`, `daily`, `aprender`; agentes `analista`, `revisor`, `validador`; hooks `guard` (proteções do perfil) e `contexto` (resumo do projeto no início da sessão); scripts determinísticos (`perfil.py`, `plano.py`, `servico.py`, `http_lote.py`, `token_login.py`); modelos de documento. |
| **azure-boards** | Skill `boards`: item raiz e tasks a partir de `tarefas.json`, estados, descrição do card — limitado ao item raiz do perfil. |
| **azure-pipelines** | Skill `pipeline` + modelos YAML (dotnet, front, sql, deploy por ambiente). |
| **stack-dotnet** | Convenções, armadilhas e checklist de revisão .NET; modelo `ApiEmMemoria.cs` para testes de contrato. |
| **stack-sql** | Convenções SQL Server (idempotência, rollback pareado, lote) + modelos de script e rollback. |
| **stack-front** | Convenções de front, verificação visual no navegador (desktop e mobile), checklist. |
| **design** | Skill `design` e agente `designer`: direção visual, tema claro/escuro com tokens, telas e fluxos, animações limpas, acessibilidade e revisão visual; modelos `tokens.css` e `movimento.css`. |
| **logs** | Skill `logs` e agente `analista-de-logs`: interface no navegador (`gui.py`) ou script. Um arquivo, vários, ou vários zips e tars. Separa erro, falso positivo e falso negativo, conta os retornos HTTP e mostra o painel. |

Instale o `fluxo` sempre; os demais conforme o projeto. As skills de stack são carregadas pelo ciclo da tarefa conforme `stacks` do perfil.

## Instalação

```bash
claude plugin marketplace add C:/caminho/para/dev-flow
claude plugin install fluxo@dev-flow
claude plugin install stack-dotnet@dev-flow
```

Quando o repositório tiver remoto (Azure Repos), troque o caminho pela URL git. Para o time receber automaticamente num projeto, declare no `.claude/settings.json` versionado do projeto:

```json
{
  "extraKnownMarketplaces": { "dev-flow": { "source": { "source": "git", "url": "<url do repositório>" } } },
  "enabledPlugins": { "fluxo@dev-flow": true, "stack-dotnet@dev-flow": true }
}
```

Atualizar depois de mudar o plugin: `claude plugin marketplace update dev-flow`.

Boards: o plugin `azure-boards` usa o MCP do Azure DevOps já configurado na máquina (`claude mcp add azure-devops -- cmd /c npx -y @azure-devops/mcp <org> -d core work work-items`). Sem ele, o fluxo roda com `rastreador.tipo = local` (tudo em `tarefas.json`).

## Manual de uso

### 1. Projeto novo (uma vez)
1. Abra o Claude Code na pasta do projeto (pode estar vazia).
2. `/fluxo:iniciar`: detecta a stack (.NET, SQL, front), cria `.claude/projeto.json` (perfil), um `CLAUDE.md` enxuto e faz `git init` se precisar.
3. Revise o `projeto.json`: comandos de build/teste, como validar e o que é proibido mexer.

### 2. Cada demanda
Tudo de uma vez: `/fluxo:entregar` e explique a demanda em texto livre. Ou passo a passo:

| Comando | Gera | Você |
| --- | --- | --- |
| `/fluxo:demanda` | `01-funcional.md` (regras, critérios de aceite, dúvidas) | responde as dúvidas e aprova |
| `/fluxo:tecnica` | `02-tecnica.md` (desenho em cima do código real) | aprova |
| `/fluxo:plano` | `tarefas.json` + `03-plano.md` (tarefas pequenas, em ordem) | aprova |
| `/fluxo:task todas` | por tarefa: implementa, testa, revisa, valida, commita | acompanha |
| `/fluxo:pr` | `pr.md` (descrição do PR) | push e PR, se houver remoto |

Nada é implementado antes das três aprovações.

### 3. No dia a dia
- `/fluxo:status`: onde paramos e o que falta.
- `/fluxo:task` (próxima) ou `/fluxo:task T3` (específica).
- `/fluxo:daily`: relatório da daily.
- `/fluxo:aprender`: transforma uma correção ("isso não é assim") em regra durável.

### 4. Regras fixas
- Push, merge e deploy em produção são do usuário (o guard bloqueia `git push`).
- Boards é opcional: só com `rastreador.tipo = azure-boards` no perfil; sem isso, tudo fica em `tarefas.json`.
- Mudança de processo para todos os projetos → este repositório. Mudança de um projeto só → `projeto.json` ou `CLAUDE.md` dele. Vale a partir da próxima sessão.

### 5. Publicar no Azure Boards
Pré-requisitos: plugin `azure-boards` instalado e MCP do Azure DevOps configurado (ver [Instalação](#instalação)).

**Configurar o projeto (uma vez):** preencher `rastreador` no `.claude/projeto.json` (ou pedir "configura o Boards neste projeto, iteração X"):

```json
"rastreador": {
  "tipo": "azure-boards",
  "org": "https://dev.azure.com/minha-organizacao",
  "projeto": "MeuProjeto",
  "area": "MeuProjeto\\Equipe",
  "iteracao": "MeuProjeto\\Sprint 12",
  "responsavel": "fulano@exemplo.com",
  "item_raiz": null,
  "protegidos": [],
  "estados": { "a_fazer": "To Do", "andamento": "In Progress", "feito": "Done" }
}
```

`item_raiz` vazio → o PBI é criado a partir da funcional. PBI que já existe → coloque o número; se ele já tem tasks, peça "importa o PBI 2000" para trazê-las ao `tarefas.json`.

**O que acontece no fluxo:**

| Momento | No Boards |
| --- | --- |
| `/fluxo:plano` aprovado | mostra a lista de PBI e tasks e só cria depois do "sim" |
| Início de cada tarefa | move a task para "In Progress" |
| Fim de cada tarefa | publica a descrição do card (implementação, testes, validação) e marca Done |
| `/fluxo:status` | compara o Boards com o `tarefas.json` e aponta divergências |

**Pedidos avulsos:** "cria os cards no Boards", "publica o card da T3", "move a task 2010 para In Progress".

**Limites:** só o PBI do perfil e as tasks filhas; itens em `protegidos` não são tocados; sem `rastreador` (ou `tipo: local`) nada vai para o Azure.

## O perfil do projeto

Tudo o que é específico de um projeto fica em `.claude/projeto.json` (schema: [`plugins/fluxo/schema/projeto.schema.json`](plugins/fluxo/schema/projeto.schema.json)); as skills não têm nada fixo. `/fluxo:iniciar` detecta a stack e cria o perfil. Exemplo real: [`exemplos/ponte/projeto.json`](exemplos/ponte/projeto.json).

| Seção | Para quê | Quem usa |
| --- | --- | --- |
| `stacks`, `convencoes` | Quais skills de stack e quais arquivos de convenção valem | task, técnica, revisor |
| `docs` | Onde ficam as especificações e `tarefas.json` | todas as skills, hook de contexto |
| `rastreador` | Local ou Azure Boards (org, item raiz, protegidos, estados) | plano, task, status, boards |
| `comandos` | build, teste, lint, vulnerabilidades | task, pr, pipeline |
| `servico`, `validacao` | Subir a aplicação, token, URL, dados de teste, casos obrigatórios, máscaras | validador, scripts |
| `git` | Branch base, formato do commit, coautor, push humano | task, pr, guard |
| `protecao` | Textos/diretórios proibidos, arquivos gerados, segredos | guard (bloqueio real) |
| `pare_e_pergunte` | Situações do projeto em que o ciclo para | task |
| `design` | Arquivo de tokens, design system, plataformas (web, ios, android, desktop) e referências de marca | design |

## Documentos de uma demanda

```
{docs}/{slug}/
  00-demanda.md     texto original do pedido
  01-funcional.md   RN, RF, critérios de aceite (CA-n), fora de escopo, dúvidas
  02-tecnica.md     componentes, contratos, dados, testes por CA, riscos, implantação
  03-plano.md       ordem, paralelismo, definição de pronto
  tarefas.json      fila (fonte da verdade): id, critérios, dependências, estado, wi, commit
  cards/{id}.html   descrição final de cada tarefa
  pr.md             descrição do PR
```

Como são arquivos, o contexto sobrevive a compactações e a sessões novas: o hook de contexto mostra a demanda ativa e a próxima tarefa ao abrir a sessão.

## Desenvolvimento do plugin

```bash
python -m unittest discover -s tests
claude plugin validate .
```

Conceitos (rules, skills, agentes, hooks, MCP, plugins e quando usar cada um): [`docs/conceitos.md`](docs/conceitos.md). Migração da Ponte: [`docs/migracao-projeto-piloto.md`](docs/migracao-projeto-piloto.md). Novo plugin de stack: [`docs/novo-plugin-de-stack.md`](docs/novo-plugin-de-stack.md).
