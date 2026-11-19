---
name: revisor-promise-sem-await
description: Revisor aponta promise não aguardada em forEach assíncrono
tags: [revisor, comportamento]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Agent]
---

Aja como o especialista `revisor` do plugin fluxo (no Claude Code, o subagente `fluxo:revisor`; em outro host, siga `agents/revisor.md`). Não há repositório: revise só o diff abaixo, de um projeto Node.js 24 com Express 5 e Prisma. Critério de aceite da tarefa: "CA-1 — ao fechar o pedido, todos os itens ficam com estado `faturado` antes da resposta 200".

```diff
--- a/src/pedidos/fechar.ts
+++ b/src/pedidos/fechar.ts
@@ -10,6 +10,12 @@ export async function fecharPedido(req: Request, res: Response) {
   const pedido = await prisma.pedido.findUniqueOrThrow({ where: { id: req.params.id }, include: { itens: true } });
+  pedido.itens.forEach(async (item) => {
+    await prisma.item.update({ where: { id: item.id }, data: { estado: "faturado" } });
+  });
+  await prisma.pedido.update({ where: { id: pedido.id }, data: { estado: "fechado" } });
   res.status(200).json({ id: pedido.id });
 }
```

Devolva os achados com arquivo:linha e severidade.
