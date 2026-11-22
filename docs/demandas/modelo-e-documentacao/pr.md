## Modelo por especialista e MCP de documentação

Gasta menos com os especialistas que não precisam do modelo mais forte, sem perder acerto (escolha por medição), e dá aos agentes a documentação da versão em uso por MCP — opcional, ligado pelo humano.

### O que muda
| Tarefa | O que muda para o consumidor | Commit |
| --- | --- | --- |
| T1 | `scripts/avaliar_agentes.py` lê a saída JSON do CLI (`result`, `total_cost_usd`) e mostra o custo do agente e do juiz por caso e no total; texto puro continua valendo. | `4a34df8` |
| T2 | Casos de comportamento do `analista` (raio de impacto de campo renomeado, com parceiro externo) e do `depurador` (data UTC × local que só falha à noite). | `70fe02e` |
| T3 | `model` por família em todos os especialistas, pela [medição](medicao.md): `analista` → `haiku`; `revisor`, `depurador`, `testador` → `sonnet`; `arquiteto`, `seguranca`, `validador`, `designer`, `analista-de-logs` → `inherit`. | `22bd9a9` |
| T4 | Catálogo datado `fluxo/referencias/documentacao.md` (Microsoft Learn para .NET/SQL Server/PowerShell; Context7 para bibliotecas em geral) e `fluxo/scripts/mcp_documentacao.py --host claude|cursor`, que gera a configuração para as stacks do perfil. `iniciar` oferece; o usuário grava. | `56e2d87` |
| T5 | README ("Custo e modelos", "Documentação por MCP"), manual, `hosts.md`, CLAUDE.md; `fluxo` 0.5.0, `design` 0.1.2, `logs` 0.1.10. | `0806856` |
| — | Correções da revisão e da segurança (guard em chamadas `mcp__*`, juiz isolado, erros com custo, árvore de processos no tempo esgotado). | `cfd5f3c` |

### Medição (22/11/2026, 7 casos × 2 execuções, juiz `opus`)
| | haiku | sonnet | opus |
| --- | --- | --- | --- |
| Casos aprovados | 6/7 (testador 1/2) | 7/7 | 7/7 |
| Custo só do agente (estimado) | ≈ 15% do opus | ≈ 54% do opus | 100% |

### Impacto em consumidores
- Claude Code: `analista`, `revisor`, `depurador` e `testador` passam a rodar em modelo mais barato que o da sessão (se a sessão estiver no opus). Para mudar um especialista no projeto: `.claude/agents/<nome>.md` com o mesmo nome. Outros hosts: nada muda.
- Guard (Claude Code) passa a olhar chamadas `mcp__*`: segredo conhecido numa consulta é bloqueado.
- MCP de documentação: nada é ligado sozinho.

### Como foi validado
- 135 testes; `claude plugin validate . --strict`; `sincronizar_hosts.py --check`; `atualizar_conhecimento.py --verificar`.
- Suíte de comportamento real nos três modelos (custo total da medição ≈ US$ 12, agente + juiz) e conferência dos verificadores novos (2/2 cada).
- Revisão pelo especialista revisor e passada do especialista de segurança; achados corrigidos em `cfd5f3c` (B4, `analista` no haiku com Bash, aceito: o guard segue valendo e a técnica revisa o que ele traz).
- Não testado: o gerador no Windows e a configuração gravada no Cursor (só formato, pela documentação oficial).

### Implantação
- Merge e `claude plugin marketplace update dev-flow` (Cursor: refresh do Team Marketplace). Rollback = reverter o merge.

Especificações: `docs/demandas/modelo-e-documentacao/`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
