---
name: seguranca-sql-concatenado
description: Segurança aponta injeção de SQL com correção parametrizada
tags: [seguranca, comportamento]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Agent]
---

Aja como o especialista `seguranca` do plugin fluxo em modo revisão (no Claude Code, o subagente `fluxo:seguranca`; em outro host, siga `agents/seguranca.md`). Não há repositório: revise só o trecho abaixo, de uma API FastAPI com psycopg 3.

```python
# app/relatorios.py
@router.get("/relatorios/vendas")
def vendas(cliente: str, conn=Depends(conexao)):
    sql = f"SELECT data, valor FROM vendas WHERE cliente = '{cliente}' ORDER BY data"
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()
```

Devolva os achados priorizados com arquivo:linha e a correção.
