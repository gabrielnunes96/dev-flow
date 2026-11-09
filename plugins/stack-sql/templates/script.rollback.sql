/*
  Rollback de: AAAAMMDD_NN_descricao.sql
  Desfaz exatamente o script, na ordem inversa, e também é idempotente.
  Atenção: remover tabela/coluna apaga dados. Se houver dados a preservar, faça backup antes (SELECT INTO dbo.Exemplo_bkp_AAAAMMDD).
*/
SET NOCOUNT ON;
SET XACT_ABORT ON;

IF OBJECT_ID(N'dbo.Exemplo_Listar', N'P') IS NOT NULL
    DROP PROCEDURE dbo.Exemplo_Listar;

IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Exemplo_Ativo' AND object_id = OBJECT_ID(N'dbo.Exemplo'))
    DROP INDEX IX_Exemplo_Ativo ON dbo.Exemplo;

IF COL_LENGTH(N'dbo.Exemplo', N'Descricao') IS NOT NULL
    ALTER TABLE dbo.Exemplo DROP COLUMN Descricao;

IF OBJECT_ID(N'dbo.Exemplo', N'U') IS NOT NULL
    DROP TABLE dbo.Exemplo;
