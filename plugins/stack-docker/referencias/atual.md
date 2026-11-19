# Conhecimento atual: Docker
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=docker-engine -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://docs.docker.com/engine/release-notes/
- https://docs.docker.com/build/release-notes/
- https://endoflife.date/docker-engine (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| docker-engine | 29 | suportado | 2025-11-10 | — | — | 29.10.0 |
| docker-engine | 25.0 | suportado | 2024-01-19 | — | 2026-12-04 | 25.0.18 |
| docker-engine | 28 | sem suporte | 2025-02-20 | — | 2026-05-13 | 28.5.2 |
| docker-engine | 27 | sem suporte | 2024-06-25 | — | 2025-05-03 | 27.5.1 |
<!-- versoes:fim -->

## O que acompanhar
- Versão do Engine/BuildKit nos agentes de CI; sintaxe do Dockerfile (`# syntax=`).
- Imagens base: tag com suporte da linguagem (ver `atual.md` da stack da linguagem).

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
