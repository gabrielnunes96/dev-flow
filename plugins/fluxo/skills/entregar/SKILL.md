---
name: entregar
description: Conduz uma demanda de ponta a ponta — funcional, técnica, plano, todas as tarefas, PR e pipeline — parando nos portões de aprovação do usuário. Use quando o usuário passar uma demanda e pedir para "fazer tudo", "levar até o PR" ou automatizar o fluxo inteiro.
argument-hint: "[descrição da demanda ou slug existente]"
---

# Demanda de ponta a ponta

Esta skill só orquestra: cada etapa é a skill correspondente, com os portões dela. Retoma de onde parou olhando os arquivos em `{docs}/{slug}/`.

| Etapa | Pronto quando | Skill |
| --- | --- | --- |
| 1. Funcional | `01-funcional.md` aprovada | `fluxo:demanda` |
| 2. Técnica | `02-tecnica.md` aprovada | `fluxo:tecnica` |
| 3. Plano | `tarefas.json` válido e `03-plano.md` aprovado | `fluxo:plano` |
| 4. Tarefas | `plano.py proxima` diz "fila concluída" | `fluxo:task todas` |
| 5. PR | `pr.md` pronto (e PR aberto, se o usuário fizer o push) | `fluxo:pr` |
| 6. Pipeline | pipeline verde ou falhas diagnosticadas | `azure-pipelines:pipeline` |

## Regras
- Descobrir a etapa atual pelos arquivos (aprovação no topo, estados em tarefas.json) e começar dali. Dizer ao usuário em uma linha onde está.
- **Portões são do usuário**: não aprovar funcional/técnica/plano por ele, nem "assumir aprovado" para ganhar tempo. Entre portões, seguir sem pedir confirmação.
- Enquanto espera um portão, nada de implementar à frente.
- Push, merge e deploy em produção são do usuário.
- Ao terminar cada etapa, uma linha de status: etapa, artefato, próximo passo.
- No fim: sugerir `/fluxo:aprender` para registrar o que esta demanda ensinou.
