---
type: llm
---

PASS se a recomendação principal é implementável no .NET 8 que o projeto usa (ex.: cache em memória ou distribuído com invalidação/expiração, considerando as 2 instâncias) e qualquer atualização de versão do .NET aparece como sugestão ou risco separado (ex.: fim de suporte), não como pré-requisito da solução.
FAIL se a solução depender de atualizar o .NET ou de recurso que não existe no .NET 8 sem dizer isso.
