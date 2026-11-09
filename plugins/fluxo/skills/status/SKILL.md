---
name: status
description: Recapitulação de uma demanda a partir de tarefas.json, git e (se houver) do rastreador — o que foi feito, o que falta, divergências, bloqueios e próximos passos. Use quando o usuário pedir recap, status, onde paramos ou resumo do andamento.
argument-hint: "[slug] [artifact]"
---

# Status da demanda

1. **Plano**: `plano.py resumo` e `plano.py tabela` da demanda (ativa ou do argumento). Etapa atual do fluxo pelos arquivos (funcional/técnica/plano aprovados?).
2. **Git**: `git log --oneline {git.branch_base}..HEAD -- .`, commits sem push (`@{u}..HEAD`, se houver upstream) e `git status --short`.
3. **Rastreador** (se azure-boards): estados dos WIs da demanda pela skill `azure-boards:boards`. Só os itens da demanda.
4. **Cruzar**: tarefa feita sem commit, commit sem tarefa, estado local ≠ rastreador → divergências.

## Formato (direto)
- **Objetivo** (1 frase, da funcional).
- **Etapa** e tabela de contagem (feitas / em andamento / a fazer / bloqueadas / protegidas).
- **Entregue**: uma linha por tarefa com o que muda para quem usa.
- **Divergências** e **bloqueios** (só o que impede de verdade; instabilidade de ambiente é observação).
- **Próximos passos** na ordem do plano.

Com `artifact`: publicar a mesma recapitulação como página (carregar `artifact-design` antes), sem tokens nem dados sensíveis.
