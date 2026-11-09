# {Título da demanda} — Plano de desenvolvimento

> Demanda: `{slug}` · Base: técnica v{n} · {dd/mm/aaaa} · Situação: **rascunho | aprovado em dd/mm/aaaa**
> Fonte da verdade das tarefas: `tarefas.json` (este arquivo traz a tabela gerada por `plano.py tabela` e a narrativa).

## Ordem e paralelismo
- Sequência obrigatória (ex.: migration → API → front) e o motivo.
- Tarefas que podem rodar em paralelo (sem dependência entre si e em arquivos diferentes).

## Tarefas
{tabela gerada por `python -I <scripts>/plano.py tabela tarefas.json`}

## Definição de pronto (vale para toda tarefa)
1. Critérios de aceite da tarefa cobertos por teste.
2. Suíte de testes verde (`comandos.teste` do perfil).
3. Revisão sem achado grave pendente.
4. Validação no ambiente (`validacao` do perfil) registrada, ou o motivo de não validar.
5. Commit único da tarefa no formato do perfil.
6. Card/tarefas.json atualizado com implementação, testes e validação.

## Riscos de execução
O que pode travar a fila (acesso, ambiente instável, decisão pendente) e o plano B.
