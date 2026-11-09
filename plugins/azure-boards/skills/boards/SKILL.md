---
name: boards
description: Opera o Azure Boards para o fluxo — criar o item raiz e as tasks a partir de tarefas.json, mover estados, publicar a descrição do card e ler o andamento — sempre limitado ao item raiz do perfil. Use quando o ciclo da tarefa, o plano ou o status precisarem do Boards, ou quando o usuário pedir para criar/atualizar cards.
argument-hint: "[criar | mover <wi> <estado> | publicar <wi> <html> | ler]"
---

# Azure Boards

Configuração: `rastreador` do perfil (`org`, `projeto`, `area`, `iteracao`, `responsavel`, `item_raiz`, `protegidos`, `estados`).

## Acesso
- Preferir as ferramentas do MCP do Azure DevOps (`mcp__azure-devops__wit_work_item`, `wit_work_item_write`, `wit_query`). Se não estiverem na sessão: `az boards` (com `PYTHONIOENCODING=utf-8`, senão o az descarta acentos) ou dizer ao usuário como adicionar o MCP:
  `claude mcp add azure-devops -- cmd /c npx -y @azure-devops/mcp <org> -d core work work-items`
- Sem nenhum dos dois → não inventar: manter tudo em `tarefas.json` e avisar.

## Limites (não negociáveis)
- **Escopo**: só o `item_raiz` e os filhos dele. Não consultar nem editar outros itens, nem configuração de board/processo/área.
- Itens em `protegidos` (e tarefas `protegida: true`): não mover, não editar.
- Toda atualização usa o teste de revisão (`test` em `/rev` com a revisão lida antes), para não sobrescrever edição concorrente.
- Criar/editar card é visível para o time: no `criar`, mostrar a lista ao usuário e só criar depois do "sim".

## Operações
- **criar**: se `item_raiz` vazio, criar o PBI com o título da demanda e a descrição = objetivo + critérios de aceite da funcional; gravar o id no perfil (`rastreador.item_raiz`) e em `tarefas.json`. Para cada tarefa sem `wi`: criar Task filha (título sem prefixo, descrição = Origem (critérios) + Padrão (convenção a seguir), area/iteração/responsável do perfil, estado `estados.a_fazer`) e gravar com `plano.py marcar <arq> <id> a_fazer --wi <n>`.
- **mover**: estado do perfil (`estados.andamento`/`feito`), uma chamada.
- **publicar**: descrição = original + Implementação + Testes + Validação (HTML do card) **e** estado `feito` numa única atualização. Guardar cópia local em `{docs}/{slug}/cards/{id}.html`.
- **ler**: filhos do `item_raiz` com id, título, estado; cruzar com `tarefas.json` e apontar divergência.
- **importar**: projeto que já tem o trabalho no Boards (ex.: PBI existente) → gerar `{docs}/{slug}/tarefas.json` com uma tarefa por filho (`id` = `T<wi>`, `wi`, título, estado mapeado de `estados`, `protegida` para os de `protegidos`, `criterios` = ["descrição do card"] quando não houver funcional). Validar com `plano.py validar`.

## Convenções de card que funcionaram
- Títulos curtos, no termo de domínio do projeto, sem prefixo ("API genérica:", "[Back]").
- Pendência que depende do usuário → registrar no card e no fechamento, não decidir.
- Task nova criada pelo usuário entra na fila na ordem de id; trazê-la para `tarefas.json` antes de executar.
