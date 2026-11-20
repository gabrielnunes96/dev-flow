---
name: testador-valores-limite
description: Testador cobre os valores-limite da regra de desconto
tags: [testador, comportamento]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Agent]
---

Aja como o especialista `testador` do plugin fluxo (no Claude Code, o subagente `fluxo:testador`; em outro host, siga `agents/testador.md`). Não há repositório: só desenhe a matriz de testes (não escreva código).

Regra (CA-1 a CA-3): pedido com total abaixo de 100,00 não tem desconto; de 100,00 até 499,99, desconto de 10%; a partir de 500,00, desconto de 20%; total negativo é rejeitado com erro de validação. Valores com duas casas decimais.
