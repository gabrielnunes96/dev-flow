---
name: mysql
description: Convenções para escrever, testar e revisar mudanças em MySQL e MariaDB no fluxo — migrations com rollback, DDL online (ALGORITHM=INSTANT/INPLACE, gh-ost/pt-osc), utf8mb4 e collation, InnoDB e transações, índices justificados por EXPLAIN, upsert, alteração em lote, modo SQL estrito e validação só em base de desenvolvimento. Use ao criar ou revisar migrations, consultas, índices ou cargas num projeto com stack mysql.
---

# MySQL / MariaDB no fluxo

As convenções do **projeto** (ferramenta de migração, pastas) vencem estas quando conflitarem.

Versões com suporte, LTS e mudanças recentes: `../../referencias/atual.md` (veja a data de revisão). Antes de usar API ou recurso, siga o procedimento *projeto primeiro* do fluxo (`referencias/conhecimento.md` do plugin `fluxo`): padrão do projeto → versão em uso → documentação daquela versão → novidade como sugestão.

## Escrever
- **Pela ferramenta de migração do projeto** (Flyway, Liquibase, Alembic, Prisma, Laravel, Rails…), uma migração por mudança, nunca editando migração aplicada. Lembre: **DDL no MySQL faz commit implícito** — uma migração com várias DDLs não é atômica; prefira uma DDL por migração e um rollback por passo.
- Idempotência à mão: `CREATE TABLE IF NOT EXISTS`, `DROP ... IF EXISTS`; para coluna/índice (sem `IF NOT EXISTS` no MySQL) consulte `information_schema` antes. MariaDB aceita `ADD COLUMN IF NOT EXISTS`.
- **DDL online**: declare `ALGORITHM=INSTANT` (8.0+, adicionar coluna) ou `ALGORITHM=INPLACE, LOCK=NONE` para o MySQL recusar em vez de copiar a tabela travando. Tabela grande sem suporte online → `gh-ost`/`pt-online-schema-change`, decisão registrada na técnica.
- Charset `utf8mb4` com a collation do projeto (`utf8mb4_0900_ai_ci` no 8.0); `utf8` (utf8mb3) corta emoji. Collation `_ci` torna comparação e `UNIQUE` sem distinção de maiúsculas/acentos — confira se é o desejado.
- Tipos: `DECIMAL(p,s)` para dinheiro, `DATETIME(3)`/`TIMESTAMP` com fuso tratado na aplicação (gravar em UTC), `BIGINT UNSIGNED AUTO_INCREMENT` ou UUID binário (`BINARY(16)`) para chave, `JSON` só quando sem esquema (com coluna gerada + índice para filtrar).
- Modo SQL estrito (`STRICT_TRANS_TABLES`, `ONLY_FULL_GROUP_BY`): não conte com truncamento silencioso nem `GROUP BY` frouxo.
- Upsert: `INSERT ... ON DUPLICATE KEY UPDATE` (cuidado: incrementa o auto_increment e afeta qualquer `UNIQUE`).
- DML volumoso em lotes (`DELETE ... WHERE ... ORDER BY id LIMIT 5000` em laço) para não estourar undo log nem atrasar réplicas.
- Concorrência: InnoDB `REPEATABLE READ` por padrão; `SELECT ... FOR UPDATE` em leitura-modificação-escrita; gap locks podem causar deadlock — trate retry de deadlock (erro 1213) na aplicação.
- Índice justificado por `EXPLAIN`/`EXPLAIN ANALYZE` (8.0.18+); ordem das colunas do índice composto segue igualdade → intervalo → ordenação.
- Consultas parametrizadas; sem `SELECT *` em código; `ORDER BY` quando a ordem importa.

## Validar (validacao.tipo = sql)
- **Só** na base de desenvolvimento/local do perfil. Conexão que não é claramente de desenvolvimento → parar e perguntar. Nunca produção.
- Sequência: migrar → conferir → reaplicar (idempotência) → rollback → conferir → migrar de novo.
- `mysql --defaults-extra-file=<arquivo local de dev> <base> < script.sql` (senha fora da linha de comando).

## Checklist de revisão
1. Migração nova, uma DDL por passo, com rollback.
2. DDL com `ALGORITHM`/`LOCK` declarados ou ferramenta online para tabela grande.
3. `utf8mb4`; collation conferida para `UNIQUE` e comparação.
4. `DECIMAL` para dinheiro; datas em UTC.
5. Lote em alteração volumosa; nenhum `UPDATE`/`DELETE` sem `WHERE`.
6. Índice justificado por consulta; composto na ordem certa.
7. Retry de deadlock onde há transação concorrente; consultas parametrizadas.
