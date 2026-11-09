---
name: sql
description: Convenções para escrever, testar e revisar scripts SQL Server no fluxo — idempotência, rollback pareado, transação e tratamento de erro, alteração em lote, índices e validação só em base de desenvolvimento. Use ao criar ou revisar scripts de banco, migrations, procedures, views ou cargas num projeto com stack sql.
---

# SQL Server no fluxo

As convenções do **projeto** (CLAUDE.md: pastas, numeração, schema) vencem estas quando conflitarem.

## Escrever
- **Um script por mudança**, com nome ordenável: `scripts/AAAAMMDD_NN_descricao.sql` e o par `rollback/AAAAMMDD_NN_descricao.rollback.sql` (modelos em `../../templates/`, relativo a esta skill).
- **Idempotente**: rodar duas vezes não falha nem duplica. `IF NOT EXISTS` / `OBJECT_ID(...) IS NULL` / `COL_LENGTH(...) IS NULL` para DDL; `CREATE OR ALTER` para procedure/view/function; `MERGE` ou `WHERE NOT EXISTS` para carga de domínio.
- DML em `BEGIN TRY / BEGIN TRAN ... COMMIT / END TRY BEGIN CATCH ROLLBACK; THROW; END CATCH`, com `SET XACT_ABORT ON`.
- **Volume**: UPDATE/DELETE em tabela grande → lotes (`TOP (5000)` em loop) para não escalar lock nem encher o log; informar a estimativa de linhas na técnica.
- Coluna nova em tabela existente: anulável ou com `DEFAULT` nomeado (`DF_Tabela_Coluna`); nada de `NOT NULL` sem default em tabela com dados.
- Nomes explícitos de constraint e índice (`PK_`, `FK_`, `IX_`, `UQ_`, `DF_`), schema sempre qualificado (`dbo.Tabela`).
- Sem `SELECT *` em código que fica (procedure/view); sem SQL dinâmico concatenado com entrada (usar `sp_executesql` com parâmetros).
- Índice novo justificado por consulta (citar a consulta); considerar `ONLINE = ON` quando a edição permitir.
- Dados sensíveis (cartão, CPF): nunca em script de carga versionado; mascarar em consultas de validação.

## Validar (validacao.tipo = sql)
- **Só** na base de desenvolvimento/local declarada no perfil. Conexão que não é claramente de desenvolvimento → parar e perguntar. Nunca produção.
- Sequência: aplicar → conferir (consulta do critério de aceite) → aplicar de novo (idempotência) → rollback → conferir que voltou → aplicar de novo (o rollback deixa reaplicar).
- `sqlcmd -S <servidor> -d <base> -E -b -i <script>` (`-b` faz erro virar código de saída). Registrar a saída resumida na tabela do card.

## Checklist de revisão
1. Rollback pareado existe e desfaz exatamente o script.
2. Idempotente (DDL com verificação, procedure com `CREATE OR ALTER`).
3. Transação + `XACT_ABORT` + `THROW` no catch em DML.
4. Lote em alteração volumosa; nenhum `DELETE`/`UPDATE` sem `WHERE`.
5. Constraints e índices nomeados; schema qualificado.
6. Sem SQL dinâmico concatenado; sem `SELECT *` persistido; sem dado sensível.
7. Compatibilidade: coluna removida/renomeada ainda usada por algum consumidor (buscar no código).
