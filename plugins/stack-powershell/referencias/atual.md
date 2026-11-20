# Conhecimento atual: PowerShell
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=powershell -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a edição e a versão do projeto mandam.

## Fontes oficiais
- https://learn.microsoft.com/powershell/scripting/install/powershell-support-lifecycle
- https://learn.microsoft.com/powershell/scripting/whats-new/overview
- https://github.com/PowerShell/PowerShell/releases
- https://github.com/PowerShell/PSScriptAnalyzer/releases
- https://github.com/pester/Pester/releases
- https://endoflife.date/powershell (suporte e fim de vida do PowerShell 7; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| powershell | 7.7 | suportado | 2026-11-10 | — | 2028-11-14 | 7.7.0 |
| powershell | 7.6 | LTS | 2026-03-18 | — | 2028-11-14 | 7.6.10 |
| powershell | 7.5 | sem suporte | 2025-01-23 | — | 2026-11-10 | 7.5.13 |
| powershell | 7.4 | sem suporte | 2023-11-16 | — | 2026-11-10 | 7.4.22 |
<!-- versoes:fim -->

Windows PowerShell 5.1 não aparece na tabela: vem com o Windows, segue o ciclo do sistema operacional e não recebe recursos novos. Ferramentas levantadas em 2026-11-19 nas fontes acima: PSScriptAnalyzer 1.25.0, Pester 6.2.0.

## O que acompanhar
- Versão do `pwsh` nos runners de CI e servidores; edição exigida pelos scripts (`#Requires`).
- Mudanças de comportamento do Pester entre versões maiores (sintaxe de `Should` e `Mock`).

## Mudanças a observar
- 2026-11-19 · a partir do PowerShell 7.2 · stderr de executável nativo redirecionado não vira mais erro sob `$ErrorActionPreference = 'Stop'` (antes, e no Windows PowerShell 5.1, encerrava o script). Fonte: https://learn.microsoft.com/powershell/scripting/whats-new/what-s-new-in-powershell-72
- 2026-11-19 · a partir do PowerShell 7.4 · `$PSNativeCommandUseErrorActionPreference` estável (código de saída diferente de 0 vira erro) e PSResourceGet (`Install-PSResource`) embutido; no 5.1 é preciso instalar o módulo. Fonte: https://learn.microsoft.com/powershell/scripting/whats-new/what-s-new-in-powershell-74
