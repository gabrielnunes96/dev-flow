---
name: arquiteto-novidade-como-sugestao
description: Arquiteto respeita a versão do projeto e trata atualização à parte
tags: [arquiteto, comportamento]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Agent]
---

Aja como o especialista `arquiteto` do plugin fluxo (no Claude Code, o subagente `fluxo:arquiteto`; em outro host, siga `agents/arquiteto.md`). Não há repositório: use só o contexto abaixo.

Contexto: API ASP.NET Core com `TargetFramework` `net8.0`, um único serviço, SQL Server, implantado em 2 instâncias atrás de um balanceador. O perfil tem `conhecimento.novidades = "sugerir"`. Demanda: "a consulta de catálogo de produtos (muda 1 vez por dia, 2 mil itens) está lenta; reduzir a latência do GET /catalogo de 900 ms para menos de 100 ms".

Recomende a solução com trade-offs.
