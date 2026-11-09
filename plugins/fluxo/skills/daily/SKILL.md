---
name: daily
description: Gera o relatório da daily (ontem, situação, hoje, impedimentos) a partir dos commits, de tarefas.json e das decisões pendentes, e salva em .claude/local para sobreviver a compactações. Use quando o usuário pedir o relatório ou a fala da daily.
argument-hint: "[data]"
---

# Relatório da daily

1. **Ontem**: commits desde o último dia útil (`git log --since=... --oneline`) cruzados com as tarefas (`tarefas.json`) e o que foi feito nesta conversa sem commit (ex.: cards, especificações). Uma linha por entrega, dizendo o que muda para quem usa — não o arquivo alterado.
2. **Situação**: `plano.py resumo`; commits locais/sem push; PR aberto?
3. **Hoje**: próximas tarefas prontas (`plano.py prontas`), portões esperando aprovação, decisões pendentes registradas nos cards, alinhamentos com consumidores.
4. **Impedimentos**: só o que impede de verdade. Ambiente instável ou limitação conhecida = "Observação". Confira em `validacao.dados` antes de chamar algo de impedimento.

Salvar em `.claude/local/daily-{aaaa-mm-dd}.md` (modelo `../../templates/daily.md`) e responder com uma **versão falada** curta (5 a 8 linhas) para ler na reunião.
