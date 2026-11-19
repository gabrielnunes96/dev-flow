# Conhecimento atual: PostgreSQL
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=postgresql -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://www.postgresql.org/support/versioning/
- https://www.postgresql.org/docs/release/
- https://endoflife.date/postgresql (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| postgresql | 18 | suportado | 2025-09-25 | — | 2030-11-14 | 18.7 |
| postgresql | 17 | suportado | 2024-09-26 | — | 2029-11-08 | 17.12 |
| postgresql | 16 | suportado | 2023-09-14 | — | 2028-11-09 | 16.16 |
| postgresql | 15 | suportado | 2022-10-13 | — | 2027-11-11 | 15.20 |
| postgresql | 14 | sem suporte | 2021-09-30 | — | 2026-11-12 | 14.25 |
| postgresql | 13 | sem suporte | 2020-09-24 | — | 2025-11-13 | 13.23 |
<!-- versoes:fim -->

## O que acompanhar
- Versão principal nova anual (cinco anos de suporte) e fim de suporte; imagem e serviço gerenciado.
- Mudanças de comportamento nas release notes (seção de incompatibilidades).

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
