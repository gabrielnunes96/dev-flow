# Modelo por especialista e MCP de documentação — Plano de desenvolvimento

> Demanda: `modelo-e-documentacao` · 22/11/2026 · Situação: **aprovado em 22/11/2026** (por delegação do usuário nesta sessão)

## Ordem
T1, T2 e T4 independentes; T3 precisa de T1 e T2 (mede com custo e com os casos novos); T5 fecha.

## Tarefas
| ID | Tarefa | Stack | Depende de | Estado | WI | Commit |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | Custo na suíte de comportamento | python | — | a_fazer | — | — |
| T2 | Casos de comportamento do analista e do depurador | python | — | a_fazer | — | — |
| T3 | Medição por modelo e modelo por especialista | python | T1, T2 | a_fazer | — | — |
| T4 | Catálogo e gerador de MCP de documentação | python | — | a_fazer | — | — |
| T5 | Documentação e versões | python | T3, T4 | a_fazer | — | — |

## Definição de pronto
- Testes verdes; revisão sem achado procedente; `claude plugin validate .`; um commit por tarefa (`{mensagem} ({id})`), sem push.

## Riscos de execução
- A medição custa chamadas reais de modelo (estimativa: poucos dólares; registrada em `medicao.md`).
