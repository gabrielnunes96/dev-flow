---
name: postgres
description: Convenções para escrever, testar e revisar mudanças em PostgreSQL no fluxo — migrations idempotentes com rollback (Flyway, Liquibase, Alembic, Prisma, EF Core), DDL sem travar tabela grande (CREATE INDEX CONCURRENTLY, coluna em etapas), transações e níveis de isolamento, índices justificados por EXPLAIN, JSONB, upsert, alteração em lote e validação só em base de desenvolvimento. Use ao criar ou revisar migrations, consultas, índices, funções ou cargas num projeto com stack postgres.
---

# PostgreSQL no fluxo

As convenções do **projeto** (ferramenta de migração, pastas, schema) vencem estas quando conflitarem. SQL Server é a skill `stack-sql:sql`.

## Escrever
- **Pela ferramenta de migração do projeto** (Flyway `V__`, Liquibase, Alembic, Prisma, EF Core, Knex…), uma migração por mudança, nunca editando migração já aplicada. Sem ferramenta: par `AAAAMMDD_NN_desc.sql` + `.rollback.sql`.
- **Idempotente** quando escrito à mão: `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `CREATE OR REPLACE FUNCTION/VIEW`, `INSERT ... ON CONFLICT DO NOTHING/UPDATE`.
- **Sem travar produção**:
  - Índice em tabela com dados: `CREATE INDEX CONCURRENTLY` (fora de transação — muitas ferramentas exigem marcar a migração como não transacional). Índice inválido após falha: `DROP INDEX CONCURRENTLY` e recriar.
  - Coluna `NOT NULL` em tabela grande: adicionar anulável → preencher em lotes → `ADD CONSTRAINT ... CHECK (col IS NOT NULL) NOT VALID` → `VALIDATE CONSTRAINT` → `SET NOT NULL`. `DEFAULT` constante é barato a partir do PG 11.
  - FK nova: `NOT VALID` e depois `VALIDATE CONSTRAINT`.
  - `SET lock_timeout = '5s'` antes de DDL para não enfileirar a aplicação atrás de um lock.
  - Renomear/remover coluna usada: expandir e contrair (nova coluna, escrever nas duas, migrar leitura, remover depois em outra entrega).
- DML volumoso em lotes (`WHERE id IN (SELECT id ... LIMIT 5000)` em laço), com estimativa de linhas na técnica.
- Tipos: `timestamptz` (não `timestamp`), `numeric(p,s)` para dinheiro, `text` com `CHECK` de tamanho em vez de `varchar(n)` arbitrário, `uuid`/`bigint identity` para chaves, `jsonb` (não `json`) só para dado realmente sem esquema — com índice GIN se for filtrado.
- Nomes explícitos de constraints e índices (`pk_`, `fk_`, `ix_`, `uq_`, `ck_`), schema qualificado quando o projeto usa mais de um.
- Consultas: parâmetros (`$1`), nunca concatenação; sem `SELECT *` em código; paginação por cursor (`WHERE id > $1 ORDER BY id LIMIT n`) em listas grandes; `ORDER BY` sempre que a ordem importa.
- Concorrência: `SELECT ... FOR UPDATE` (ou `SKIP LOCKED` para filas) em leitura-modificação-escrita; isolamento acima de `READ COMMITTED` só com retry de serialização.
- Índice novo justificado por consulta e `EXPLAIN (ANALYZE, BUFFERS)` (em dev, com volume representativo). Índice que ninguém usa custa em toda escrita.

## Validar (validacao.tipo = sql)
- **Só** na base de desenvolvimento/local declarada no perfil (container do `compose` do projeto, por exemplo). Conexão que não é claramente de desenvolvimento → parar e perguntar. Nunca produção.
- Sequência: migrar → conferir (consulta do critério) → migrar de novo (idempotência/ferramenta não reaplica) → rollback/downgrade → conferir → migrar de novo.
- `psql "$URL" -v ON_ERROR_STOP=1 -f script.sql` (erro vira código de saída). Senha por `PGPASSWORD`/`.pgpass` de dev, nunca no comando versionado.

## Checklist de revisão
1. Migração nova (não edição), com rollback/downgrade que desfaz exatamente.
2. DDL em tabela grande sem lock longo (`CONCURRENTLY`, `NOT VALID` + `VALIDATE`, `lock_timeout`).
3. Tipos certos: `timestamptz`, `numeric` para dinheiro, `jsonb` justificado.
4. Lote em alteração volumosa; nenhum `UPDATE`/`DELETE` sem `WHERE`.
5. Índice justificado por consulta; consulta nova com índice que a atende.
6. Parâmetros, nunca concatenação; sem `SELECT *` persistido.
7. Expandir/contrair para mudança que quebra consumidor (buscar usos da coluna no código).
