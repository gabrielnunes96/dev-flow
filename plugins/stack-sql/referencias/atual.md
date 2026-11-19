# Conhecimento atual: SQL Server
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=mssqlserver -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://learn.microsoft.com/sql/sql-server/end-of-support/sql-server-end-of-support-overview
- https://learn.microsoft.com/sql/sql-server/what-s-new-in-sql-server
- https://endoflife.date/mssqlserver (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| mssqlserver | 17.0 | suportado | 2025-11-18 | 2031-01-06 | 2036-01-06 | 17.0.5065.9 CU11 |
| mssqlserver | 16.0 | suportado | 2022-11-16 | 2028-01-11 | 2033-01-11 | 16.0.4325.4 CU28 |
| mssqlserver | 15.0 | suportado | 2019-11-04 | 2025-02-28 | 2030-01-08 | 15.0.4510.2 CU32+GDR |
| mssqlserver | 14.0 | suportado | 2017-09-29 | 2022-10-11 | 2027-10-12 | 14.0.3570.2 CU31+GDR |
| mssqlserver | 13.0-sp3-acp | sem suporte | 2022-05-19 | 2026-07-14 | 2026-07-14 | 13.0.7095.1 Azure Connect pack+GDR |
| mssqlserver | 13.0-sp3 | sem suporte | 2021-09-15 | 2026-07-14 | 2026-07-14 | 13.0.6500.1 GDR |
<!-- versoes:fim -->

## O que acompanhar
- Fim de suporte da versão do servidor e nível de compatibilidade do banco.
- Recursos T-SQL novos só valem se o nível de compatibilidade do banco permitir.

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
