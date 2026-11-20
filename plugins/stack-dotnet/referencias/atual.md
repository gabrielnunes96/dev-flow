# Conhecimento atual: .NET
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=dotnet -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://dotnet.microsoft.com/platform/support/policy/dotnet-core
- https://learn.microsoft.com/dotnet/core/whats-new/
- https://endoflife.date/dotnet (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| dotnet | 11 | suportado | 2026-11-10 | — | 2028-11-14 | 11.0.0 |
| dotnet | 10 | LTS | 2025-11-11 | — | 2028-11-14 | 10.0.15 |
| dotnet | 9 | sem suporte | 2024-11-12 | — | 2026-11-10 | 9.0.23 |
| dotnet | 8 | sem suporte | 2023-11-14 | — | 2026-11-10 | 8.0.34 |
<!-- versoes:fim -->

## O que acompanhar
- Versão LTS nova (a cada dois anos) e fim de suporte da anterior; `TargetFramework` e `global.json`.
- Pacotes do ASP.NET Core/EF Core que mudam de comportamento entre versões principais (guias de breaking changes).

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
