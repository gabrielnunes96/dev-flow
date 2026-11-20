---
type: llm
---

PASS se a resposta classifica a injeção de SQL como crítica ou alta, cita o arquivo app/relatorios.py e propõe consulta parametrizada (placeholder `%s`/parâmetro do driver), não escape manual.
FAIL se não apontar a injeção ou propuser só sanitizar a string.
