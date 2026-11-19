## Conhecimento atualizável dos agentes

Evita que as skills e os especialistas do dev-flow fiquem defasados conforme linguagens, frameworks, bancos e modelos evoluem — sem o mantenedor precisar lembrar de revisá-los e sem o agente sair aplicando novidade num projeto que segue outro padrão. Funciona em qualquer host (Claude Code, Cursor, outros agentes com Agent Skills e CLIs).

### O que muda
| Tarefa | O que muda para o consumidor | Commit |
| --- | --- | --- |
| T1 | Procedimento *projeto primeiro* (`fluxo/referencias/conhecimento.md`): padrão do projeto → versão em uso → documentação daquela versão → novidade conforme o perfil. Campo opcional `conhecimento.novidades` (`sugerir` padrão / `aplicar`) no schema, no `perfil.py validar` e na skill `iniciar`. | `f423e8f` |
| T3 | `scripts/atualizar_conhecimento.py`: consulta endoflife.date, regenera as tabelas de versões e aponta ciclo novo, LTS novo, fim de suporte, versão sem suporte citada nos plugins (arquivo:linha), revisão vencida e falha de fonte; `--verificar` sem rede. | `6254705` |
| T4 | `plugins/stack-*/referencias/atual.md` nas 13 stacks (fontes oficiais, tabela gerada com dados reais de hoje, o que acompanhar, mudanças a observar). A primeira execução achou e corrigiu modelos sem suporte: `golang:1.23` → `1.27`, `ARG DOTNET=8.0` → `10.0` (o .NET 8 saiu de suporte em 10/11/2026) e o comentário "Spring Boot 3.3+". A tabela distingue `suporte ativo encerrado` (só segurança até o fim) de `sem suporte`. | `35cf596`, `5b5b2d8` |
| T2 | Bloco "Conhecimento atual (projeto primeiro)" em todos os especialistas do `fluxo` e no `designer` e no `analista-de-logs`; as 13 skills de stack apontam para o `atual.md` e para o procedimento; exemplos de versão na skill Docker ficaram neutros; `aprender` leva aprendizado de stack ao `atual.md` por PR. | `31ef895` |
| T5 | Suíte de comportamento `plugins/fluxo/evals/` (revisor ×2, segurança, arquiteto, testador) no formato do `claude plugin eval` e executor host-agnóstico `scripts/avaliar_agentes.py --comando "<cli>" [--juiz "<cli>"]`. | `f85a386` |
| T6 | Revisão periódica: skill de manutenção `.claude/skills/atualizar-conhecimento` (termina em branch + `pr.md`, nunca merge/push), `azure-pipelines-conhecimento.yml` e `.github/workflows/conhecimento.yml` mensais (o do GitHub abre/atualiza uma issue quando há achados), e `--verificar` + `sincronizar_hosts --check` no CI de PR. | `56cde69` |
| T7 | README (seção "Conhecimento sempre atual" e perfil), manual (seção "Conhecimento atual"), CLAUDE.md, guia de nova stack; versões: `fluxo` 0.4.0, stacks 0.2.0, `design` 0.1.1, `logs` 0.1.9, catálogo 0.4.0; manifestos do Cursor sincronizados. | (último commit da branch) |

### Impacto em consumidores
- Nada quebra: o campo `conhecimento` do perfil é opcional (ausente = `sugerir`).
- Times recebem os arquivos novos pela atualização do marketplace; quem usa skills exportadas precisa exportar de novo para levar `referencias/`.

### Como foi validado
- Testes: 121 passando (`python -m unittest discover -s tests`), incluindo os critérios CA-1 a CA-12.
- `claude plugin validate . --strict` e de cada plugin: ok. `sincronizar_hosts.py --check`: ok.
- Levantamento real contra a endoflife.date: tabelas geradas; achados reais corrigidos; segunda execução sem achados.
- Suíte de comportamento contra um modelo real: **não executada aqui** (o `claude -p` deste ambiente não está autenticado). Rodar: `python -I scripts/avaliar_agentes.py --comando "claude -p" --juiz "claude -p"` ou `claude plugin eval plugins/fluxo`.

### Pendências e decisões
- Aprovações de funcional, técnica e plano delegadas pelo usuário nesta sessão.
- "Mudanças a observar" começam vazias: a primeira revisão mensal (skill `atualizar-conhecimento`) preenche com fonte.
- Pipelines agendadas precisam ser criadas/ativadas: Azure (Pipelines → New pipeline → `azure-pipelines-conhecimento.yml`); GitHub roda sozinho depois do merge na `main`.
- Testes de comportamento não rodam por PR (custo de modelo); rodam na revisão periódica e sob demanda.

### Implantação
- Merge, subir as versões já ajustadas e `claude plugin marketplace update dev-flow` (Cursor: refresh do Team Marketplace). Rollback = reverter o merge.

Especificações: `docs/demandas/conhecimento-atualizavel/`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
