---
name: revisor-projeto-primeiro
description: Revisor não exige migrar o projeto para tecnologia nova
tags: [revisor, comportamento]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Agent]
---

Aja como o especialista `revisor` do plugin fluxo (no Claude Code, o subagente `fluxo:revisor`; em outro host, siga `agents/revisor.md`). Não há repositório: use só o contexto abaixo.

Contexto do projeto: `package.json` com `"engines": { "node": "22" }`, Express 4, JavaScript (CommonJS). Todas as rotas existentes seguem o padrão `router.get(caminho, async (req, res, next) => { try { ... } catch (e) { next(e) } })`. Perfil: `conhecimento.novidades = "sugerir"`. Critério da tarefa: "CA-1 — GET /clientes/:id/limite devolve 200 com `{ limite }` e 404 quando o cliente não existe".

```diff
--- a/src/rotas/clientes.js
+++ b/src/rotas/clientes.js
@@ -40,3 +40,13 @@ router.get('/clientes/:id', async (req, res, next) => {
+router.get('/clientes/:id/limite', async (req, res, next) => {
+  try {
+    const cliente = await repo.buscarCliente(req.params.id);
+    if (!cliente) return res.status(404).json({ erro: 'cliente não encontrado' });
+    res.status(200).json({ limite: cliente.limite });
+  } catch (e) {
+    next(e);
+  }
+});
```

Devolva os achados com arquivo:linha e severidade.
