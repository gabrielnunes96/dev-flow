# Conhecimento atual: Go
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=go -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://go.dev/doc/devel/release
- https://go.dev/blog/
- https://endoflife.date/go (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| go | 1.27 | suportado | 2026-08-19 | — | — | 1.27.4 |
| go | 1.26 | suportado | 2026-02-10 | — | — | 1.26.11 |
| go | 1.25 | sem suporte | 2025-08-12 | — | 2026-08-19 | 1.25.14 |
| go | 1.24 | sem suporte | 2025-02-11 | — | 2026-02-10 | 1.24.13 |
<!-- versoes:fim -->

## O que acompanhar
- Só as duas últimas versões principais têm suporte; diretiva `go`/`toolchain` do `go.mod`.
- Mudanças da biblioteca padrão (roteamento do net/http, iteradores, slog) e do `govulncheck`.

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
