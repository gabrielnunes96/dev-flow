# Conhecimento atual: MongoDB
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=mongodb -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://www.mongodb.com/legal/support-policy/lifecycles
- https://www.mongodb.com/docs/manual/release-notes/
- https://endoflife.date/mongodb (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| mongodb | 9.0 | suportado | 2026-09-30 | — | 2031-10-31 | 9.0.8 |
| mongodb | 8.3 | suportado | 2026-05-31 | — | 2029-10-31 | 8.3.17 |
| mongodb | 8.0 | suportado | 2024-10-31 | — | 2029-10-31 | 8.0.38 |
| mongodb | 7.0 | suportado | 2023-08-31 | — | 2027-08-31 | 7.0.48 |
| mongodb | 8.2 | sem suporte | 2025-09-30 | — | 2026-07-31 | 8.2.12 |
| mongodb | 8.1 | sem suporte | 2025-06-30 | — | 2025-09-30 | 8.1.3 |
<!-- versoes:fim -->

## O que acompanhar
- Fim de suporte da versão do servidor e `featureCompatibilityVersion`.
- Versão do driver compatível com o servidor.

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
