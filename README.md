# dev-flow

Marketplace de plugins do Claude Code com o fluxo de desenvolvimento do time: **da demanda explicada em texto até o PR e a pipeline**, com especificação funcional e técnica, plano, implementação tarefa a tarefa, revisão, segurança, validação no ambiente e CI/CD — com portões de aprovação humana e proteções que não dependem da memória do modelo.

> 📘 **Manual completo, navegável e com busca:** abra [`docs/manual/index.html`](docs/manual/index.html) no navegador.

```text
você explica a demanda
  → /fluxo:demanda   01-funcional.md   (regras, critérios de aceite)        ◆ você aprova
  → /fluxo:tecnica   02-tecnica.md     (analista + arquiteto + segurança)   ◆ você aprova
  → /fluxo:plano     tarefas.json      (tarefas pequenas, em ordem)         ◆ você aprova
  → /fluxo:task todas  por tarefa: implementa → testa → revisor (+segurança) → validador → commit
  → /fluxo:pr        pr.md  (+ PR aberto depois do seu push)
  → pipeline         CI verde; produção com aprovação no environment
/fluxo:entregar faz tudo isso em sequência, parando só nos ◆.
```

## Comece em 3 minutos

**1. Adicione o marketplace e instale o núcleo** (uma vez por máquina):

```bash
claude plugin marketplace add <caminho-ou-url-do-dev-flow>
```

```bash
claude plugin install fluxo@dev-flow
```

**2. Instale as stacks do seu projeto** (exemplo: API Node com Postgres, Docker e GitHub Actions):

```bash
claude plugin install stack-node@dev-flow
```

```bash
claude plugin install stack-postgres@dev-flow
```

```bash
claude plugin install stack-docker@dev-flow
```

```bash
claude plugin install github-actions@dev-flow
```

**3. No projeto**, abra o Claude Code e rode `/fluxo:iniciar`. Ele detecta stacks, comandos, CI e infraestrutura e cria `.claude/projeto.json`.

**4. Traga uma demanda:** `/fluxo:entregar` e explique o que precisa em texto livre. Ou um bug: `/fluxo:depurar <erro>`.

> Atualizar depois de uma mudança no marketplace: `claude plugin marketplace update dev-flow`.

## Catálogo de plugins

### Núcleo e processo
| Plugin | O que traz |
| --- | --- |
| **fluxo** | Skills `iniciar`, `demanda`, `tecnica`, `plano`, `task`, `entregar`, `pr`, `status`, `daily`, `aprender`, `depurar`, `arquitetura`. Agentes especialistas (abaixo). Hooks `guard` (bloqueios do perfil) e `contexto` (resumo do projeto ao abrir a sessão). Scripts determinísticos e modelos de documento. Método de raciocínio em `referencias/raciocinio.md`. |

### Rastreador e CI/CD
| Plugin | O que traz |
| --- | --- |
| **azure-boards** | Item raiz e tasks a partir de `tarefas.json`, estados, descrição do card — limitado ao item raiz do perfil. |
| **azure-pipelines** | YAML para dotnet, node/front, python, java, go, sql, Docker (ACR + Trivy), Terraform (plan em PR, apply com aprovação) e deploy por estágios; diagnóstico de execuções. |
| **github-actions** | Workflows de CI, imagem no GHCR com varredura e deploy por environment com OIDC; diagnóstico com `gh`. |
| **gitlab-ci** | `.gitlab-ci.yml` com verificação, testes, SAST/segredos, imagem e produção manual; diagnóstico com `glab`. |

### Linguagens
| Plugin | Cobre |
| --- | --- |
| **stack-dotnet** | ASP.NET Core, Nullable em DTOs, rotas, testes de contrato com a API em memória, SDKs gerados. |
| **stack-node** | Express, Fastify, NestJS, TypeScript estrito, zod, Prisma/TypeORM, supertest. |
| **stack-python** | FastAPI, Django, Flask, pydantic v2, SQLAlchemy/Alembic, pytest, ruff, uv/poetry. |
| **stack-java** | Spring Boot, JPA sem N+1, Bean Validation, JUnit 5, MockMvc, Testcontainers, Flyway. Kotlin incluso. |
| **stack-go** | Erros com wrap, `context`, goroutines sem vazamento, testes de tabela, `-race`, govulncheck. |
| **stack-front** | React, Angular, Vue: estados de tela, contrato com o back, verificação visual desktop e mobile. |

### Bancos de dados
| Plugin | Cobre |
| --- | --- |
| **stack-sql** | SQL Server: idempotência, rollback pareado, transação com `XACT_ABORT`, lotes. |
| **stack-postgres** | Migrations, DDL sem travar (`CONCURRENTLY`, `NOT VALID`), `timestamptz`/`numeric`, `EXPLAIN`. |
| **stack-mysql** | MySQL/MariaDB: DDL online, `utf8mb4` e collation, deadlocks, índices compostos. |
| **stack-mongodb** | Modelagem por acesso, `$jsonSchema`, índices ESR, operadores atômicos, injeção de operador. |
| **stack-redis** | Cache-aside com TTL, invalidação, locks com token, rate limit, streams, comandos proibidos. |

### Infraestrutura
| Plugin | Cobre |
| --- | --- |
| **stack-docker** | Multi-stage, base fixada, não root, `.dockerignore`, compose de dev; modelos de Dockerfile para dotnet, node, python, java e go. |
| **stack-kubernetes** | Requests/limits, probes, `securityContext`, rollout sem indisponibilidade, PDB/HPA, segredos externos; manifesto base. |
| **stack-terraform** | Estado remoto, versões fixadas, plan revisado (nunca apply pela sessão), `prevent_destroy`, `moved`/`import`. |

### Extras
| Plugin | O que traz |
| --- | --- |
| **design** | Designer de UX/UI: direção visual, tema claro/escuro com tokens, telas, animações, acessibilidade. |
| **video** | Vídeo-resumo narrado de uma entrega a partir de um roteiro JSON. |

**Qual instalar?** Sempre `fluxo`. Depois, um plugin por item de `stacks` do perfil (stack `X` → `stack-X`) e o do seu `ci.provedor`. O ciclo da tarefa carrega a skill da stack sozinho.

## Agentes especialistas

Cada agente roda em contexto isolado, com ferramentas restritas, e devolve só o resultado. As skills chamam no momento certo; você também pode pedir direto ("chama o arquiteto para…").

| Agente | Quando entra | Devolve |
| --- | --- | --- |
| `analista` | Técnica, análise de impacto | Fluxo real do dado, arquivos com linha, padrão a copiar, raio de impacto |
| `arquiteto` | Técnica com decisão estrutural; `/fluxo:arquitetura` | Alternativas com trade-offs, recomendação, ADRs prontos |
| `seguranca` | Técnica (ameaças STRIDE) e tarefa que toca auth, dados, pagamento, upload ou infra | Ameaças e mitigações; achados OWASP por severidade |
| `testador` | Tarefa com regra combinatória, cálculo ou estados | Matriz de testes (partições, limites, decisão, estados) e, se pedido, os testes |
| `revisor` | Toda tarefa, antes do commit | Achados com `arquivo:linha`, execução simulada, N+1, concorrência |
| `depurador` | `/fluxo:depurar`; teste falhando sem causa clara | Causa raiz com evidência, hipóteses testadas, teste de regressão |
| `validador` | Toda tarefa, no ambiente | Tabela de resultados (HTTP, SQL, comando ou navegador) |
| `design:designer` | Trabalho de UI à parte | Tema, telas, animações, revisão visual |

Todos seguem o **método de raciocínio** do plugin ([`plugins/fluxo/referencias/raciocinio.md`](plugins/fluxo/referencias/raciocinio.md)): modelar entrada/estado/fronteiras, contrato (pré/pós-condição e invariante), lista de casos de borda, custo (O() e I/O), execução simulada, **simplicidade sem overengineering** (nada de abstração, camada ou infraestrutura sem requisito), depuração por hipóteses e verificação antes de dizer "pronto".

## Comandos do dia a dia

| Você quer… | Comando |
| --- | --- |
| Configurar um projeto | `/fluxo:iniciar` |
| Levar uma demanda até o PR | `/fluxo:entregar <demanda>` |
| Só a especificação funcional | `/fluxo:demanda` |
| Só a técnica | `/fluxo:tecnica <slug>` |
| Quebrar em tarefas | `/fluxo:plano <slug>` |
| Próxima tarefa / uma específica / todas | `/fluxo:task` · `/fluxo:task T3` · `/fluxo:task todas` |
| Corrigir um bug pela causa raiz | `/fluxo:depurar <erro ou descrição>` |
| Registrar uma decisão de arquitetura | `/fluxo:arquitetura adr <decisão>` |
| Documentar ou revisar a arquitetura | `/fluxo:arquitetura mapa` · `/fluxo:arquitetura revisar` |
| Onde paramos? | `/fluxo:status` |
| Relatório da daily | `/fluxo:daily` |
| Descrição do PR | `/fluxo:pr` |
| Pipeline (criar, ajustar, diagnosticar) | `/azure-pipelines:pipeline` · `/github-actions:actions` · `/gitlab-ci:gitlab` |
| Transformar uma correção em regra | `/fluxo:aprender` |

## O perfil do projeto

Tudo o que é específico de um projeto fica em `.claude/projeto.json` ([schema](plugins/fluxo/schema/projeto.schema.json)); as skills não têm nada fixo. Exemplo real: [`exemplos/ponte/projeto.json`](exemplos/ponte/projeto.json).

| Seção | Para quê | Quem usa |
| --- | --- | --- |
| `stacks`, `convencoes` | Quais skills de stack e quais arquivos de convenção valem | task, técnica, revisor, testador |
| `docs` | Onde ficam especificações e `tarefas.json` | todas as skills, hook de contexto |
| `rastreador` | Local ou Azure Boards (org, item raiz, protegidos, estados) | plano, task, status, boards |
| `comandos` | restaurar, build, teste, lint, vulnerabilidades (e os que quiser) | task, pr, pipelines |
| `servico`, `validacao` | Subir a aplicação, token, URL, dados de teste, casos obrigatórios, máscaras | validador, scripts |
| `ci` | Provedor (`azure-pipelines`, `github-actions`, `gitlab-ci`), arquivos e ambientes | técnica, entregar, pr |
| `infra` | Nuvem, onde roda (kubernetes, compose, app-service…), pasta de IaC, registro, observabilidade | técnica, arquiteto, segurança |
| `git` | Branch base, formato do commit, coautor, push humano | task, pr, guard |
| `protecao` | Textos/diretórios proibidos, arquivos gerados, segredos | guard (bloqueio real) |
| `pare_e_pergunte` | Situações do projeto em que o ciclo para | task |
| `design` | Tokens, design system, plataformas, referências | design |

Valide sempre que mudar: `python -I <scripts>/perfil.py validar` (o hook de início de sessão mostra o caminho dos scripts).

## Regras fixas (garantidas por hook, não por memória)

- **Push, merge, deploy em produção e `terraform apply` são seus.** O guard bloqueia `git push` quando `git.push = humano`.
- Commit **só com o seu "pode commitar"**, uma tarefa por vez.
- Diretórios proibidos, arquivos gerados e arquivos de segredo declarados em `protecao` não são lidos nem editados.
- Commit com JWT, chave privada, chave AWS ou token do GitHub nas linhas adicionadas é bloqueado sempre.
- Nada é implementado antes das três aprovações (funcional, técnica, plano).

## Documentos de uma demanda

```text
{docs}/{slug}/
  00-demanda.md     texto original do pedido
  01-funcional.md   RN, RF, critérios de aceite (CA-n), fora de escopo, dúvidas
  02-tecnica.md     componentes, contratos, dados, segurança, testes por CA, riscos, implantação
  03-plano.md       ordem, paralelismo, definição de pronto
  tarefas.json      fila (fonte da verdade): id, critérios, dependências, estado, wi, commit
  cards/{id}.html   descrição final de cada tarefa
  pr.md             descrição do PR
{docs}/bug-{resumo}/bug.md   sintoma, hipóteses, causa raiz, correção e prova
docs/adr/NNNN-*.md            decisões de arquitetura
```

Como tudo é arquivo, o contexto sobrevive a compactações e a sessões novas: o hook de contexto mostra a demanda ativa e a próxima tarefa ao abrir a sessão.

## Azure Boards (opcional)

Pré-requisitos: plugin `azure-boards` e o MCP do Azure DevOps configurado na máquina:

```bash
claude mcp add azure-devops -- npx -y @azure-devops/mcp <org> -d core work work-items
```

No Windows: `-- cmd /c npx …`.

No perfil:

```json
"rastreador": {
  "tipo": "azure-boards",
  "org": "https://dev.azure.com/minha-organizacao",
  "projeto": "MeuProjeto",
  "area": "MeuProjeto\\Equipe",
  "iteracao": "MeuProjeto\\Sprint 12",
  "item_raiz": null,
  "protegidos": [],
  "estados": { "a_fazer": "To Do", "andamento": "In Progress", "feito": "Done" }
}
```

`item_raiz` vazio → o PBI é criado a partir da funcional; PBI existente → coloque o número ("importa o PBI 2000" traz as tasks dele). Plano aprovado cria as tasks (depois do seu "sim"); cada tarefa move para "In Progress" ao começar e para "Done" ao terminar, com a descrição do card. Só o PBI do perfil e as tasks filhas são tocados; itens em `protegidos` nunca.

## Para o time inteiro

Declare no `.claude/settings.json` versionado do projeto, e quem abrir o projeto recebe os plugins:

```json
{
  "extraKnownMarketplaces": { "dev-flow": { "source": { "source": "git", "url": "<url do repositório>" } } },
  "enabledPlugins": { "fluxo@dev-flow": true, "stack-node@dev-flow": true, "stack-postgres@dev-flow": true }
}
```

## Desenvolvimento deste repositório

```bash
python -m unittest discover -s tests
```

```bash
claude plugin validate .
```

- Mudança de comportamento de script ou hook → teste em `tests/`. Dado novo que uma skill precisa → schema + `perfil.py validar` + teste.
- Nova stack: [`docs/novo-plugin-de-stack.md`](docs/novo-plugin-de-stack.md) (o `test_marketplace.py` confere que toda stack do schema tem plugin com checklist).
- Publicar: subir `version` no `plugin.json` alterado e no `marketplace.json`.
- Conceitos (rules, skills, agentes, hooks, MCP, plugins e quando usar cada um): [`docs/conceitos.md`](docs/conceitos.md). Migração do projeto piloto: [`docs/migracao-projeto-piloto.md`](docs/migracao-projeto-piloto.md).
