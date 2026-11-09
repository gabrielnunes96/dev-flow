---
name: pr
description: Prepara o pull request de uma demanda — confere fila e branch, monta a descrição (o que muda, impacto em consumidores, validação, pendências, implantação) e, se o usuário já fez o push, abre o PR vinculado aos work items. Use quando o usuário pedir o PR, a descrição do PR ou para fechar a entrega.
argument-hint: "[slug da demanda]"
---

# Pull request da demanda

## 1. Conferir
- `plano.py resumo`: tarefas não feitas → listar e perguntar se o PR sai assim (parcial) ou espera.
- `git status --short` limpo; `git log --oneline {git.branch_base}..HEAD` — cada tarefa feita tem commit com o id; commit sem tarefa ou tarefa sem commit → apontar.
- Suíte de testes verde (rodar `comandos.teste` se a última execução não estiver nesta conversa) e, se houver, `comandos.vulnerabilidades` sem achados.

## 2. Descrição
- `{docs}/{slug}/pr.md` pelo modelo `../../templates/pr.md`: dados de `tarefas.json`, dos cards e da funcional (impacto em consumidores). Sem segredos, tokens ou dados de cartão.
- Título: o da demanda, sem prefixo.

## 3. Abrir (só depois do push do usuário)
- O push é do usuário (`git.push = humano`). Se a branch ainda não está no remoto, entregar `pr.md` e o comando de push para ele rodar.
- Com a branch no remoto e Azure DevOps: `az repos pr create --source-branch <branch> --target-branch {git.branch_base} --title ... --description @pr.md --work-items <wis>` (confirmar com o usuário antes: é ação visível para o time). GitHub: `gh pr create`.
- Depois de aberto: acompanhar a pipeline com a skill `azure-pipelines:pipeline` (ler o status, diagnosticar falha), sem habilitar auto-merge.
