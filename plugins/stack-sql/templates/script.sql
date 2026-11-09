/*
  Script:     AAAAMMDD_NN_descricao.sql
  Demanda:    {slug} / tarefa {Tn} (#WI)
  Objetivo:   {uma frase}
  Rollback:   rollback/AAAAMMDD_NN_descricao.rollback.sql
  Idempotente: sim (pode rodar mais de uma vez)
*/
SET NOCOUNT ON;
SET XACT_ABORT ON;

-- DDL: tabela nova
IF OBJECT_ID(N'dbo.Exemplo', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Exemplo
    (
        Id          INT IDENTITY(1, 1) NOT NULL CONSTRAINT PK_Exemplo PRIMARY KEY,
        Codigo      VARCHAR(20)        NOT NULL CONSTRAINT UQ_Exemplo_Codigo UNIQUE,
        Ativo       BIT                NOT NULL CONSTRAINT DF_Exemplo_Ativo DEFAULT (1),
        CriadoEm    DATETIME2(0)       NOT NULL CONSTRAINT DF_Exemplo_CriadoEm DEFAULT (SYSUTCDATETIME())
    );
END;

-- DDL: coluna nova em tabela existente (anulável ou com default nomeado)
IF COL_LENGTH(N'dbo.Exemplo', N'Descricao') IS NULL
    ALTER TABLE dbo.Exemplo ADD Descricao VARCHAR(200) NULL;

-- DDL: índice justificado pela consulta "{consulta}"
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Exemplo_Ativo' AND object_id = OBJECT_ID(N'dbo.Exemplo'))
    CREATE INDEX IX_Exemplo_Ativo ON dbo.Exemplo (Ativo) INCLUDE (Codigo);
GO

-- Procedure/view/function: CREATE OR ALTER
CREATE OR ALTER PROCEDURE dbo.Exemplo_Listar
    @Ativo BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, Codigo, Descricao, CriadoEm
    FROM dbo.Exemplo
    WHERE Ativo = @Ativo;
END;
GO

-- DML: carga de domínio idempotente, em transação
BEGIN TRY
    BEGIN TRAN;

    INSERT INTO dbo.Exemplo (Codigo, Descricao)
    SELECT v.Codigo, v.Descricao
    FROM (VALUES ('A', 'Exemplo A'), ('B', 'Exemplo B')) AS v (Codigo, Descricao)
    WHERE NOT EXISTS (SELECT 1 FROM dbo.Exemplo e WHERE e.Codigo = v.Codigo);

    COMMIT;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    THROW;
END CATCH;
GO

-- DML volumoso: em lotes
-- DECLARE @lote INT = 5000, @afetadas INT = 1;
-- WHILE @afetadas > 0
-- BEGIN
--     UPDATE TOP (@lote) dbo.Tabela SET Coluna = 'x' WHERE Coluna IS NULL;
--     SET @afetadas = @@ROWCOUNT;
-- END;
