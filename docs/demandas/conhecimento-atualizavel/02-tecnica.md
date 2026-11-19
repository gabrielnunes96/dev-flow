# Conhecimento atualizável dos agentes — Especificação técnica

> Demanda: `conhecimento-atualizavel` · Versão 1 · 19/11/2026 · Situação: **aprovada em 19/11/2026** (por delegação do usuário nesta sessão)
> Funcional: `01-funcional.md` (aprovada em 19/11/2026)

## 1. Visão da solução
Quatro peças, todas texto + scripts só com biblioteca padrão, sem depender de host (RN-8):

```text
método (estável)                 conhecimento volátil (datado)             verificação
skills stack-* e agents/*.md ──▶ plugins/stack-X/referencias/atual.md ◀── scripts/atualizar_conhecimento.py
        │                         (fontes, versões geradas, mudanças)          │  fonte: endoflife.date
        ▼                                                                       ▼
fluxo/referencias/conhecimento.md  (projeto primeiro)          relatório ──▶ skill de manutenção ──▶ branch + PR (humano aprova)
                                                                              │
                                    plugins/fluxo/evals/<agente>/<caso>/ ◀────┘  scripts/avaliar_agentes.py (qualquer CLI)
                                                                              ou claude plugin eval (atalho no Claude Code)
```

## 2. Componentes afetados
| Componente | Mudança |
| --- | --- |
| `plugins/fluxo/referencias/conhecimento.md` (novo) | Procedimento "projeto primeiro": convenções → versão em uso → documentação daquela versão → novidade conforme `conhecimento.novidades`. Como consultar documentação em qualquer host (MCP de documentação se houver; senão busca web; senão documentação/fonte local dos pacotes instalados; senão dizer que não confirmou). |
| `plugins/stack-*/referencias/atual.md` (13 novos) | Metadados em comentário (`revisado_em`, `produtos`), Fontes oficiais, bloco gerado de versões, Mudanças a observar (curadoria). |
| `plugins/stack-*/skills/*/SKILL.md` | Uma linha após "convenções do projeto vencem": aponta para `../../referencias/atual.md` e para o procedimento do fluxo. |
| `plugins/fluxo/agents/*.md`, `plugins/design/agents/designer.md`, `plugins/logs/agents/*.md` | Bloco curto "Conhecimento atual" com os 4 passos (autocontido, para funcionar mesmo sem resolver caminho). |
| `plugins/fluxo/referencias/hosts.md` | Cita `conhecimento.md`. |
| `plugins/fluxo/schema/projeto.schema.json`, `scripts/perfil.py` | `conhecimento.novidades` ∈ {`sugerir`, `aplicar`}, opcional (padrão `sugerir`). |
| `plugins/fluxo/skills/aprender/SKILL.md` | Linha "vale para qualquer projeto daquela stack" → proposta ao `referencias/atual.md` ou à skill do plugin da stack, via PR no dev-flow. |
| `plugins/fluxo/skills/iniciar/SKILL.md` | Perguntar/inferir `conhecimento.novidades` (projeto novo → `aplicar`; existente → `sugerir`). |
| `scripts/atualizar_conhecimento.py` (novo) | Levantamento online, verificação offline, relatório. |
| `scripts/avaliar_agentes.py` (novo) | Executor host-agnóstico da suíte de comportamento. |
| `plugins/fluxo/evals/` (novo) | Casos no formato do `claude plugin eval` (`prompt.md` + `graders/*.md`), agrupados por especialista. |
| `.claude/skills/atualizar-conhecimento/SKILL.md` (novo) | Skill de manutenção do repositório (Claude Code e Cursor leem `.claude/skills/`; outros hosts: apontar para o arquivo). |
| `azure-pipelines-conhecimento.yml`, `.github/workflows/conhecimento.yml` (novos) | Agendamento mensal do levantamento; relatório como artefato; no GitHub, abre/atualiza uma issue quando há achados. |
| README, manual, CLAUDE.md, `docs/novo-plugin-de-stack.md`, `.gitignore` | Documentação; `plugins/*/evals/results/` ignorado. |

## 3. Contratos
**`referencias/atual.md`**
```text
# Conhecimento atual: <Stack>
<!-- dev-flow:conhecimento revisado_em=AAAA-MM-DD produtos=prod1,prod2 -->
> Gerado em parte por scripts/atualizar_conhecimento.py ...
## Fontes oficiais         (≥ 1 link)
## Versões                 <!-- versoes:inicio --> tabela gerada <!-- versoes:fim -->
## Mudanças a observar     curadoria (data + fonte por item)
```
`revisado_em` = última revisão humana da curadoria. A tabela traz "gerado em AAAA-MM-DD".

**`atualizar_conhecimento.py`**
- `--verificar [--max-dias N=120]`: offline; estrutura + revisão vencida. Saída 0 ok / 1 problema.
- (padrão) online: para cada stack, busca `https://endoflife.date/api/<produto>.json` (timeout 20 s), regrava o bloco de versões, compara com o bloco anterior e varre `plugins/**` (md, yml, Dockerfile, templates) por versões citadas. `--relatorio <arq>`, `--sem-gravar`, `--fonte-dir <dir>` (lê `<produto>.json` local; usado nos testes), `--stack X` (repetível). Saída 0 sem achados / 2 com achados / 1 erro geral.
- Achados: `novo_ciclo`, `fim_de_suporte` (ciclo com `eol` ≤ hoje que antes não estava), `novo_lts`, `versao_sem_suporte` (arquivo:linha), `falha_fonte` (produto), `revisao_vencida`.

**`avaliar_agentes.py`**
- `--comando "<cmd>"` (ex.: `claude -p`, `cursor-agent -p`, `codex exec`); o prompt vai por stdin; com `{prompt_arquivo}` no comando, vai por arquivo. `--juiz "<cmd>"` opcional para graders `llm` (responde PASS/FAIL). `--caso <glob>`, `--plugin <nome>` (padrão todos com `evals/`), `--execucoes N`, `--listar`.
- Prompt enviado = corpo do `agents/<agente>.md` + caso (o diretório pai do caso é o agente). Graders `regex` aplicados à saída; `llm` só com `--juiz`; outros tipos → "não avaliado" (não falham).
- Saída 0 todos os casos aprovados / 1 algum reprovado ou erro.

**Perfil**: `"conhecimento": { "novidades": "sugerir" | "aplicar" }`.

## 4. Dados
Sem banco. Arquivos novos versionados; relatórios e resultados de avaliação ficam fora do git.

## 5. Integrações externas
- endoflife.date (API pública, sem chave). Falha por produto não interrompe nem grava parcial (CA-6).
- Agentes de linha de comando escolhidos por quem roda a avaliação (custo de modelo é de quem roda).
- GitHub (workflow): `GITHUB_TOKEN` com `issues: write`, só para abrir/atualizar issue.

## 6. Segurança
- Nenhum segredo nos scripts; `avaliar_agentes.py` executa o comando passado pelo próprio usuário (sem shell de texto vindo de arquivo de caso). Prompts de caso não são executados como comando.
- Conteúdo baixado é JSON tratado como dado; campos convertidos para texto e escapados de `|` na tabela.
- A skill de manutenção proíbe merge, push forçado e publicação; termina em branch + `pr.md`.
- Workflow do GitHub com permissões mínimas (`contents: read`, `issues: write`).

## 7. Observabilidade
Relatório Markdown (achados por stack) publicado como artefato do pipeline/issue; o executor de avaliação imprime tabela caso × resultado e pode gravar JSON (`--json`).

## 8. Estratégia de testes
| CA | Teste |
| --- | --- |
| CA-1, CA-2, CA-10, CA-12 | `tests/test_conhecimento.py`: estrutura dos `atual.md`, citação nas skills de stack e agentes, texto da `aprender`, ausência de dependência de host sem alternativa. |
| CA-3 | `tests/test_perfil.py`: `conhecimento.novidades` válido/inválido/ausente. |
| CA-4, CA-5, CA-6 | `test_conhecimento.py` com `--fonte-dir` (JSON fixo, um produto ausente) e `hoje` injetado. |
| CA-7 | verificação offline com data vencida → código 1. |
| CA-8 | existência e conteúdo mínimo dos YAML e da skill de manutenção. |
| CA-9, CA-11 | `tests/test_avaliar_agentes.py`: estrutura dos casos (frontmatter permitido do `claude plugin eval`, tipos de grader, regex compila, agente existe) e execução com comando falso (`python -c`). |
| Regressão | `python -m unittest discover -s tests`, `claude plugin validate .`, `sincronizar_hosts.py --check`. |

## 9. Riscos e decisões
- **D1 — Fonte de versões: endoflife.date.** Cobre todas as 13 stacks (testado: dotnet, nodejs, python, eclipse-temurin, spring-boot, go, react, angular, vue, mssqlserver, postgresql, mysql, mariadb, mongodb, redis, docker-engine, kubernetes, terraform, django). Alternativa (raspar changelogs) descartada: frágil. Risco: indisponibilidade → falha por produto, sem gravação.
- **D2 — Curadoria só com aprovação humana** (RN-4): o robô gera relatório; o LLM só propõe texto numa branch.
- **D3 — Formato dos casos = formato do `claude plugin eval`**, com executor próprio para outros hosts: uma fonte, dois executores (RN-8). Graders `tool_used` não entram nos casos (dependem do host).
- **D4 — Bloco autocontido nos agentes** em vez de só um link: agentes exportados/vendorizados nem sempre resolvem caminhos.
- **D5 — Skill de manutenção em `.claude/skills/`** (lida por Claude Code e Cursor); não vai no plugin `fluxo` porque só faz sentido neste repositório.
- Risco: "Mudanças a observar" começa vazia nas stacks — preenchida pela primeira revisão; a tabela de versões já sai com dados reais.

## 10. Implantação e rollback
Publicação normal do marketplace (subir versões, `sincronizar_hosts.py`). Rollback = reverter o commit; campo de perfil é opcional, então perfis existentes seguem válidos.

## 11. CI/CD
- `azure-pipelines.yml` (PR) ganha `atualizar_conhecimento.py --verificar` e `sincronizar_hosts.py --check` se ainda não houver.
- Pipelines agendadas novas (Azure e GitHub) rodam o levantamento mensalmente. Testes de comportamento não rodam por PR (custo); rodam na revisão periódica, sob demanda.
