# Conhecimento atualizável dos agentes — Plano de desenvolvimento

> Demanda: `conhecimento-atualizavel` · 19/11/2026 · Situação: **aprovado em 19/11/2026** (por delegação do usuário nesta sessão)
> Funcional e técnica aprovadas em 19/11/2026.

## Ordem e paralelismo
T1 e T3 começam juntas. T2 depende de T1; T4 precisa do texto das skills (T2) e do script (T3); T5 depende de T2; T6 de T3 e T5; T7 fecha.

## Tarefas
| ID | Tarefa | Stack | Depende de | Estado | WI | Commit |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | Procedimento projeto primeiro e política de novidades no perfil | python | — | a_fazer | — | — |
| T2 | Bloco de conhecimento atual nos especialistas e nas skills de stack | python | T1 | a_fazer | — | — |
| T3 | Script atualizar_conhecimento.py com testes | python | — | a_fazer | — | — |
| T4 | Arquivos atual.md das 13 stacks | python | T2, T3 | a_fazer | — | — |
| T5 | Suíte de comportamento e executor host-agnóstico | python | T2 | a_fazer | — | — |
| T6 | Revisão periódica: skill de manutenção e pipelines agendadas | python | T3, T5 | a_fazer | — | — |
| T7 | Documentação, versões e sincronização dos hosts | python | T4, T6 | a_fazer | — | — |

## Definição de pronto (vale para toda tarefa)
- Critérios da tarefa cobertos por teste em `tests/`.
- `python -m unittest discover -s tests` verde.
- Revisão pelo especialista `revisor` sem achado procedente aberto.
- Validação do perfil (`claude plugin validate . && python -m unittest discover -s tests`).
- Um commit por tarefa (`{mensagem} ({id})`), sem push.

## Riscos de execução
- endoflife.date fora do ar na hora de gerar T4 → gerar depois; o script não grava parcial.
- Execução real da suíte de comportamento custa chamada de modelo → opcional nesta entrega; os testes do repositório usam comando falso.
