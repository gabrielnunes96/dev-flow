# Bug: {resumo do sintoma}

> Slug: `{slug}` · Aberto em dd/mm/aaaa · Situação: **investigando | causa encontrada | corrigido em {hash} | não reproduz**

## Sintoma
Literal: mensagem, stack trace (sem segredos), esperado × obtido.

## Reprodução
Comando ou passo a passo mínimo, com dados de teste. Ambiente (local, hml, prd), versão/commit, desde quando.

## Investigação
| Hipótese | Teste feito | Resultado |
| --- | --- | --- |
| | | confirmada / derrubada |

## Causa raiz
`arquivo:linha` — por que acontece (causa) e o que expôs agora (gatilho).

## Correção
O que mudou e por que é a causa, não o sintoma. Commit: `{hash}`.

## Prova
- Teste de regressão: `{arquivo de teste}::{nome}` — falhava antes, passa depois.
- Validação no ambiente: {resultado ou "pendente: motivo"}.

## Prevenção
Regra, teste ou proteção que evita a repetição (e onde foi registrada).
