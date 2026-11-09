---
name: plano
description: Quebra a especificação técnica aprovada em tarefas pequenas, ordenadas e verificáveis (tarefas.json + 03-plano.md), com dependências, stack, critérios de aceite e validação de cada uma; opcionalmente cria o item raiz e as tasks no rastreador. Use quando o usuário pedir o plano de desenvolvimento, a quebra em tasks/cards ou o backlog de uma demanda.
argument-hint: "[slug da demanda]"
---

# Técnica → plano e tarefas

## 1. Pré-condições
- `02-tecnica.md` **aprovada**. Não aprovada → parar.

## 2. Quebrar
Regras de corte (as mesmas que funcionaram na Ponte):
- **Uma tarefa = um commit = uma entrega verificável.** Cabe em uma sessão; se precisa de "e também", são duas.
- Tarefa vertical por operação/funcionalidade (contrato + implementação + teste), não horizontal por camada.
- Toda tarefa aponta para critérios de aceite (`criterios`); critério sem tarefa = buraco no plano.
- Mudança transversal (renomear, padronizar, atualizar pacote) é tarefa própria, separada das funcionais.
- Dependência só quando é real (o código de uma precisa do da outra). O resto pode correr em paralelo.
- Tarefa em mais de um repositório → uma por repositório, com dependência.
- `validacao` diz o que será chamado/executado e o resultado esperado.

## 3. Gravar
- `{docs}/{slug}/tarefas.json` no formato de `../../templates/tarefas.json` (ids T1..Tn, `estado: a_fazer`).
- `python -I ../../scripts/plano.py validar <arq>` até sair "tarefas ok".
- `03-plano.md` pelo modelo, com a tabela de `plano.py tabela <arq>`, ordem/paralelismo e riscos.

## 4. Portão
- Mostrar ao usuário a tabela e a ordem. Aprovação → "aprovado em dd/mm/aaaa" no topo.

## 5. Rastreador (só se `rastreador.tipo = azure-boards`)
- Com o plano aprovado, delegar à skill `azure-boards:boards` (`criar`): item raiz (se `item_raiz` vazio) e uma task por tarefa, gravando o `wi` de volta em tarefas.json. Sem o plugin ou sem conexão → manter local e avisar.
- Sugerir `/fluxo:task todas` (ou `/fluxo:entregar` para seguir até o PR).
