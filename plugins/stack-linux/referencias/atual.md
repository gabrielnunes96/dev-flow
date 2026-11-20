# Conhecimento atual: Linux
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=ubuntu,debian,rhel,alpine-linux -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a distribuição e a versão do projeto mandam.

## Fontes oficiais
- https://ubuntu.com/about/release-cycle
- https://www.debian.org/releases/
- https://access.redhat.com/support/policy/updates/errata
- https://alpinelinux.org/releases/
- https://endoflife.date/ubuntu, https://endoflife.date/debian, https://endoflife.date/rhel, https://endoflife.date/alpine-linux (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| ubuntu | 26.10 | suportado | 2026-10-15 | 2027-07-01 | 2027-07-01 | 26.10 |
| ubuntu | 26.04 | LTS | 2026-04-23 | 2031-05-29 | 2031-05-29 | 26.04.1 |
| ubuntu | 24.04 | LTS | 2024-04-25 | 2029-05-31 | 2029-05-31 | 24.04.5 |
| ubuntu | 22.04 | LTS | 2022-04-21 | 2024-09-30 | 2027-06-01 | 22.04.5 |
| ubuntu | 25.10 | sem suporte | 2025-10-09 | 2026-07-01 | 2026-07-01 | 25.10 |
| ubuntu | 25.04 | sem suporte | 2025-04-17 | 2026-01-17 | 2026-01-17 | 25.04 |
| debian | 13 | suportado | 2025-08-09 | 2028-08-09 | 2030-06-30 | 13.7 |
| debian | 12 | suporte ativo encerrado | 2023-06-10 | 2026-07-11 | 2028-06-30 | 12.15 |
| debian | 11 | sem suporte | 2021-08-14 | 2024-08-14 | 2026-08-31 | 11.11 |
| debian | 10 | sem suporte | 2019-07-06 | 2022-09-10 | 2024-06-30 | 10.13 |
| rhel | 10 | suportado | 2025-05-20 | 2030-05-31 | 2035-05-31 | 10.3 |
| rhel | 9 | suportado | 2022-05-18 | 2027-05-31 | 2032-05-31 | 9.9 |
| rhel | 8 | suporte ativo encerrado | 2019-05-07 | 2024-05-31 | 2029-05-31 | 8.10 |
| rhel | 7 | sem suporte | 2014-06-10 | 2019-08-06 | 2024-06-30 | 7.9 |
| rhel | 6 | sem suporte | 2010-11-10 | 2016-05-10 | 2020-11-30 | 6.10 |
| alpine-linux | 3.24 | suportado | 2026-06-09 | — | 2028-06-01 | 3.24.4 |
| alpine-linux | 3.23 | suportado | 2025-12-04 | — | 2027-11-01 | 3.23.8 |
| alpine-linux | 3.22 | suportado | 2025-05-30 | — | 2027-05-01 | 3.22.8 |
| alpine-linux | 3.21 | sem suporte | 2024-12-05 | — | 2026-11-01 | 3.21.10 |
| alpine-linux | 3.20 | sem suporte | 2024-05-22 | — | 2026-04-01 | 3.20.10 |
<!-- versoes:fim -->

"Fim de suporte" é o suporte padrão gratuito; Ubuntu (ESM/Pro), Debian (LTS/ELTS) e RHEL (ELS) oferecem extensões — contar com elas é decisão do projeto, registrada como risco.

## O que acompanhar
- Distribuição e versão das imagens base, dos runners de CI (`ubuntu-<versão>`) e dos servidores.
- Codinomes nas tags de imagem (`-bookworm`, `-jammy`) também envelhecem: a varredura do levantamento os reconhece.

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
