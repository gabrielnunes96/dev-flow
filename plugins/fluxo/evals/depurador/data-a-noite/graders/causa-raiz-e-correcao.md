---
type: llm
---

PASS se a causa raiz apontada é a mistura de referências de data: o código compara com a data em UTC e o teste usa a data local, então a partir das 21h em São Paulo (UTC−3) a data UTC já é o dia seguinte e o boleto de "hoje" aparece vencido; no CI, que roda em UTC, as duas datas coincidem. E se propõe correção que usa a mesma referência nos dois lados (definir o fuso de negócio, injetar `hoje`/relógio) com um teste de regressão que fixa o horário.
FAIL se culpar intermitência genérica, ambiente de CI, cache ou ordem dos testes, ou se não explicar por que só falha depois das 21h.
