---
name: analista-campo-renomeado
description: Analista encontra todos os consumidores de um campo de API renomeado e aponta o risco de contrato
tags: [analista, comportamento]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Agent]
---

Aja como o especialista `analista` do plugin fluxo (no Claude Code, o subagente `fluxo:analista`; em outro host, siga `agents/analista.md`). Não há repositório: analise só os arquivos abaixo, de um projeto .NET com front em React. Requisito: "RF-1 — a resposta de `GET /pedidos/{id}` passa a chamar o campo `valor` de `valorTotal`".

`src/Api/Pedidos/PedidoResposta.cs`
```csharp
public sealed record PedidoResposta(Guid Id, string Cliente, decimal Valor, DateTime CriadoEm);
```

`src/Api/Pedidos/PedidosController.cs`
```csharp
[HttpGet("{id:guid}")]
public async Task<ActionResult<PedidoResposta>> Obter(Guid id) =>
    await _servico.Obter(id) is { } p ? Ok(new PedidoResposta(p.Id, p.Cliente, p.Total, p.CriadoEm)) : NotFound();
```

`web/src/pedidos/DetalhePedido.tsx`
```tsx
const { data: pedido } = useQuery(["pedido", id], () => api.get<Pedido>(`/pedidos/${id}`));
return <span>{formatarMoeda(pedido?.valor ?? 0)}</span>;
```

`web/src/pedidos/tipos.ts`
```ts
export interface Pedido { id: string; cliente: string; valor: number; criadoEm: string; }
```

`docs/integracoes.md`
```md
## Parceiro Logística Sul
Consome `GET /pedidos/{id}` a cada despacho e lê `valor` para calcular o seguro da carga. Contrato público, sem versão no caminho.
```

Devolva a análise de impacto no formato do especialista.
