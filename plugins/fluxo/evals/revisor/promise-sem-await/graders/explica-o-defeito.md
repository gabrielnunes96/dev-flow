---
type: llm
---

PASS se a resposta aponta como defeito que o `forEach(async ...)` não aguarda as atualizações (a resposta 200 pode sair antes dos itens ficarem `faturado`, violando o CA-1) e propõe `for...of` com `await`, `Promise.all` ou `updateMany`/transação.
FAIL se não apontar esse defeito ou se o tratar como mero estilo.
