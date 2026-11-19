# Conhecimento atual: MySQL/MariaDB
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=mysql,mariadb -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://dev.mysql.com/doc/relnotes/mysql/en/
- https://mariadb.org/about/#maintenance-policy
- https://endoflife.date/mysql (suporte e fim de vida; fonte da tabela abaixo)
- https://endoflife.date/mariadb (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| mysql | 26.10 | suportado | 2026-10-20 | sim | — | 26.10.0 |
| mysql | 9.7 | LTS | 2026-04-21 | 2031-04-30 | 2034-04-30 | 9.7.4 |
| mysql | 8.4 | LTS | 2024-04-30 | 2029-04-30 | 2032-04-30 | 8.4.13 |
| mysql | 26.7 | sem suporte | 2026-07-28 | 2026-10-20 | 2026-10-20 | 26.7.1 |
| mysql | 9.6 | sem suporte | 2026-01-20 | 2026-04-21 | 2026-04-21 | 9.6.1 |
| mariadb | 13.0 | suportado | 2026-09-15 | — | 2026-12-31 | 13.0.2 |
| mariadb | 12.3 | LTS | 2026-05-28 | — | 2029-06-12 | 12.3.4 |
| mariadb | 11.8 | LTS | 2025-06-04 | — | 2028-06-04 | 11.8.10 |
| mariadb | 11.4 | LTS | 2024-05-29 | — | 2029-05-29 | 11.4.14 |
| mariadb | 10.11 | LTS | 2023-02-16 | — | 2028-02-16 | 10.11.20 |
| mariadb | 12.2 | sem suporte | 2026-02-13 | — | 2026-05-28 | 12.2.2 |
| mariadb | 12.1 | sem suporte | 2025-11-18 | — | 2026-02-13 | 12.1.2 |
<!-- versoes:fim -->

## O que acompanhar
- Linhas LTS e Innovation do MySQL e fim de suporte; versão do serviço gerenciado.
- LTS do MariaDB; diferenças de sintaxe entre MySQL e MariaDB.

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
