# Stacks de Bash, Git e Linux — Plano de desenvolvimento

> Demanda: `stacks-bash-git-linux` · 19/11/2026 · Situação: **aprovado em 19/11/2026** (por delegação do usuário nesta sessão)

## Ordem
T1 primeiro (formato `produtos=-` e codinomes); T2, T3 e T4 dependem de T1; T5 fecha.

## Tarefas
| ID | Tarefa | Stack | Depende de |
| --- | --- | --- | --- |
| T1 | Levantamento: stack sem produto e codinomes de distribuição | python | — |
| T2 | Plugin stack-bash | python | T1 |
| T3 | Plugin stack-git | python | T1 |
| T4 | Plugin stack-linux | python | T1 |
| T5 | Perfil, detecção, catálogo, documentação e versões | python | T2, T3, T4 |
| T6 | Plugin stack-powershell (complemento) | python | T5 |

## Definição de pronto
- Testes verdes; revisão sem achado procedente; `claude plugin validate .`; um commit por tarefa (`{mensagem} ({id})`), sem push.
