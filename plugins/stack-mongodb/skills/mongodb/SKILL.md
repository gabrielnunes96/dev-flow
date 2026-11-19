---
name: mongodb
description: Convenções para modelar, implementar, testar e revisar com MongoDB no fluxo — modelagem por padrão de acesso (embutir × referenciar), validação de esquema ($jsonSchema), índices compostos pela regra ESR, migrações de documentos, transações multi-documento, operadores atômicos, agregações, paginação e injeção de operadores. Use ao criar ou revisar coleções, consultas, agregações, índices ou migrações num projeto com stack mongodb.
---

# MongoDB no fluxo

As convenções do **projeto** (ODM — Mongoose, Spring Data, Motor/Beanie, driver oficial —, pastas de migração) vencem estas quando conflitarem.

Versões com suporte, LTS e mudanças recentes: `../../referencias/atual.md` (veja a data de revisão). Antes de usar API ou recurso, siga o procedimento *projeto primeiro* do fluxo (`referencias/conhecimento.md` do plugin `fluxo`): padrão do projeto → versão em uso → documentação daquela versão → novidade como sugestão.

## Modelar
- **Modele pelo padrão de acesso**, não pela normalização: liste as consultas da funcional e desenhe o documento para que a principal leia **um** documento.
- Embutir quando o filho só existe com o pai, é lido junto e é limitado (endereços de um cliente). Referenciar quando cresce sem limite (pedidos de um cliente), é compartilhado ou atualizado sozinho. Array que cresce sem limite é bug futuro (documento máximo de 16 MB, reescrita cara).
- Validação no banco com `$jsonSchema` (`validationLevel: moderate` ao introduzir em coleção com dados) **e** na aplicação (schema do ODM/zod/pydantic).
- `_id`: `ObjectId` por padrão; chave natural só se for imutável e única. Datas como `Date` em UTC; dinheiro como `Decimal128` (ou inteiro em centavos), nunca `double`.
- Campo de versão do esquema (`schemaVersion`) quando o formato do documento muda ao longo do tempo.

## Implementar
- Atualizações atômicas com operadores (`$set`, `$inc`, `$push` com `$slice`, `$addToSet`), não ler-modificar-gravar o documento inteiro. Controle otimista com campo de versão no filtro (`{_id, version}`) quando dois escritores podem colidir.
- Transação multi-documento (replica set) só quando a regra exige atomicidade entre documentos; prefira desenhar para um documento. Na transação, use a mesma sessão em todas as operações e trate `TransientTransactionError` com retry.
- `upsert: true` com filtro por chave única (índice `unique`) para idempotência.
- Paginação por intervalo (`{_id: {$gt: ultimo}}` + `sort` + `limit`), não `skip` grande.
- Projeção explícita (só os campos usados). Agregações: `$match` e `$sort` cedo (para usar índice), `$lookup` com moderação, `allowDiskUse` consciente.
- **Injeção de operador**: entrada do usuário nunca vira objeto de filtro direto (`{email: req.body.email}` aceita `{"$ne": null}`). Valide o tipo (string) ou use `$eq`. Nunca `$where`/`$function` com entrada.
- Migração de dados: script versionado (migrate-mongo, Mongock, script próprio) idempotente, em lotes, com rollback ou estratégia de leitura dos dois formatos.

## Índices
- Todo filtro/ordenação de consulta nova tem índice. Composto pela regra **ESR**: campos de **E**quality, depois **S**ort, depois **R**ange.
- Confirme com `explain("executionStats")`: `IXSCAN`, não `COLLSCAN`; `totalDocsExamined` próximo de `nReturned`.
- Índice novo em coleção grande: criação em produção é operação planejada (impacto em réplica); registre na técnica. TTL para dado que expira; `unique` para chave de negócio; parcial/esparso quando o campo é opcional.

## Testar
- `comandos.teste` com MongoDB real de teste (Testcontainers ou o do `compose`); evite mocks do driver para consultas e agregações — o erro está no pipeline.
- Teste da validação de esquema (documento inválido é recusado), do índice `unique` (duplicado falha) e da concorrência quando há controle otimista.
- Validação (`validacao.tipo = sql`/`comando`): só na base de desenvolvimento; nunca produção.

## Checklist de revisão
1. Documento desenhado pelo acesso; nenhum array sem limite.
2. Operadores atômicos; sem ler-modificar-gravar sem controle de versão.
3. Entrada validada por tipo antes de virar filtro; sem `$where` com entrada.
4. Índice para cada consulta nova, na ordem ESR, confirmado por `explain`.
5. Paginação por intervalo; projeção explícita.
6. Datas UTC, dinheiro em `Decimal128`/centavos.
7. Migração de documentos idempotente e em lotes; aplicação lê o formato antigo durante a transição.
