# Conhecimento atual: Node.js
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=nodejs -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://nodejs.org/en/about/previous-releases
- https://github.com/nodejs/Release
- https://endoflife.date/nodejs (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| nodejs | 26 | LTS | 2026-05-05 | 2027-10-27 | 2029-04-30 | 26.13.1 |
| nodejs | 24 | LTS | 2025-05-06 | 2026-10-20 | 2028-04-30 | 24.22.3 |
| nodejs | 22 | LTS | 2024-04-24 | 2025-10-21 | 2027-04-30 | 22.23.5 |
| nodejs | 25 | sem suporte | 2025-10-15 | 2026-04-01 | 2026-06-01 | 25.9.0 |
| nodejs | 23 | sem suporte | 2024-10-16 | 2025-04-01 | 2025-06-01 | 23.11.1 |
<!-- versoes:fim -->

## O que acompanhar
- Troca de LTS ativo (anual) e fim de suporte; `.nvmrc`/`engines`/imagem base.
- Recursos que passam de experimental a estável (test runner, módulos, APIs web nativas).

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
