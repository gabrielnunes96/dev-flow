---
name: powershell
description: Convenções para escrever, testar e revisar scripts e módulos PowerShell no fluxo — PowerShell 7 (pwsh) multiplataforma e Windows PowerShell 5.1, modo estrito e erros terminantes, código de saída de executáveis nativos, funções avançadas com parâmetros tipados e validados, -WhatIf/-Confirm em quem altera, saída em objetos no pipeline, caminhos e codificação, segredos com PSCredential/SecretManagement, módulos com manifesto, PSScriptAnalyzer e Pester. Use ao criar ou revisar arquivos .ps1, .psm1 ou .psd1, automação Windows, passos de CI em PowerShell ou scripts de implantação num projeto com stack powershell.
---

# PowerShell no fluxo

As convenções do **projeto** (edição e versão alvo, módulos corporativos, regras do PSScriptAnalyzer, política de assinatura) vencem estas quando conflitarem. Modelo: `../../templates/script.ps1` (relativo a esta skill).

Versões com suporte, LTS e mudanças recentes: `../../referencias/atual.md` (veja a data de revisão). Antes de usar API ou recurso, siga o procedimento *projeto primeiro* do fluxo (`referencias/conhecimento.md` do plugin `fluxo`): padrão do projeto → versão em uso → documentação daquela versão → novidade como sugestão.

## Escrever
- **Edição e versão alvo**: PowerShell 7 (`pwsh`, multiplataforma) ou Windows PowerShell 5.1 (`powershell.exe`, embutido no Windows, sem recursos novos). Declarar com `#Requires -Version <versão do projeto>` (e `#Requires -PSEdition Core` quando só roda no 7). Recurso só do 7 (`??`, `?.`, `ForEach-Object -Parallel`, ternário) não entra em script que roda no 5.1.
- **Modo estrito e erros**: `Set-StrictMode -Version 3.0` (versão fixa: `Latest` muda de sentido entre versões) e `$ErrorActionPreference = 'Stop'` no topo, para erro não terminante virar exceção; `try { } catch { } finally { }` onde há recuperação ou limpeza. Erro esperado: `-ErrorAction SilentlyContinue` só no comando, com o motivo comentado. Em modo estrito, `@(...)` em resultado que pode ser único antes de usar `.Count`.
- **Armadilha do `Stop` com stderr nativo**: em versões antigas (inclusive 5.1; ver `atual.md`), redirecionar o stderr de executável nativo (`git fetch 2>&1`, `2>$null`, remoting) transforma cada linha em erro e encerra o script mesmo com código 0. Nessas versões, não redirecionar stderr de nativo sob `Stop`, ou baixar a preferência só em volta da chamada e decidir por `$LASTEXITCODE`.
- **Executável nativo** (`git`, `dotnet`, `az`) não lança exceção: conferir `$LASTEXITCODE` depois de cada um, ou ligar `$PSNativeCommandUseErrorActionPreference` se a versão do projeto tiver (ver `atual.md`). Executável com códigos fora do padrão (`robocopy`: 0–7 é sucesso) → desligar essa preferência localmente em volta da chamada e avaliar o código à mão.
- **Funções avançadas**: `[CmdletBinding()]` e `param()` com tipo, `[Parameter(Mandatory)]`, `[ValidateNotNullOrEmpty()]`, `[ValidateSet()]`, `[ValidateScript()]`; comentário de ajuda (`.SYNOPSIS`, `.EXAMPLE`). Quem altera algo: `SupportsShouldProcess` e `if ($PSCmdlet.ShouldProcess(...))`, para `-WhatIf`/`-Confirm` funcionarem.
- **Nomes**: `Verbo-Substantivo` com verbo aprovado (`Get-Verb`); em script e módulo, nome completo de cmdlet e de parâmetro — sem aliases (`ls`, `%`, `?`, `iwr`) nem parâmetro posicional ambíguo.
- **Saída**: objetos no pipeline (`[pscustomobject]@{...}`), não texto formatado; `Format-*` só na ponta interativa. Mensagens: `Write-Verbose`, `Write-Warning`, `Write-Error`, `Write-Information`; `Write-Host` só para interface de console, nunca para dado. Cuidado com saída acidental (`$lista.Add(x)` devolve índice → `[void]` ou `$null = `).
- **Caminhos**: `$PSScriptRoot` e `Join-Path`, nunca caminho relativo ao diretório atual; caminho recebido vira absoluto (`Convert-Path`) antes de ir para método .NET, que usa outro diretório atual; `-LiteralPath` quando o nome pode ter `[` `]`; no Linux/macOS, maiúsculas importam e o separador é `/`.
- **Codificação**: sempre `-Encoding` explícito em `Set-Content`/`Out-File`/`Export-Csv`, sabendo que muda entre edições: no 5.1, `utf8` grava **com** BOM e `>`/`Out-File` gravam UTF-16LE; no 7, `utf8` grava **sem** BOM (com BOM é `utf8BOM`). Consumidor que exige UTF-8 sem BOM e script no 5.1 → `[IO.File]::WriteAllText($caminho, $texto, [Text.UTF8Encoding]::new($false))`. Script com acentos que roda no 5.1: salvar em UTF-8 **com BOM** (sem BOM o 5.1 lê como ANSI). Fim de linha conforme o `.gitattributes` (stack `git`).
- **Segredos**: `PSCredential`/`SecureString` vindos de `Get-Credential`, do cofre (módulo SecretManagement, Key Vault) ou de variável do CI; nunca literal no script, nem `ConvertTo-SecureString -AsPlainText` com valor fixo, nem em `Start-Transcript`/log. `SecureString` só é cifrado no Windows; no Linux/macOS o cuidado é não expor nem registrar o valor.
- **Execução de texto**: nada de `Invoke-Expression` (ou `iex`) com entrada externa; montar chamadas com splatting (`$params = @{...}; Cmd @params`) e `&` para executável.
- **Política de execução** não é fronteira de segurança: não mandar `Set-ExecutionPolicy Bypass`/`Unrestricted` global; para uma execução, `powershell.exe -ExecutionPolicy <política do projeto> -File ...` (5.1) ou `pwsh -ExecutionPolicy ... -File ...` (7); fora do Windows a política não se aplica; assinar scripts se o projeto exige (`Set-AuthenticodeSignature`).
- **Módulos**: `.psm1` + manifesto `.psd1` com `FunctionsToExport` explícito (sem `*`) e `RequiredModules` com versão; dependências instaladas de repositório confiável com versão fixa (`Install-PSResource -Version`, que vem embutido só em versões recentes — ver `atual.md` —, ou `Install-Module -RequiredVersion`), nunca de URL solta.
- **Idempotente**: checar estado antes de mudar (`Test-Path`, `Get-Service`), para rodar duas vezes sem estragar. Mudança em servidor compartilhado (serviço, IIS, registro, GPO, remoting) segue a regra da stack `linux`: a sessão prepara e testa em ambiente descartável; o humano aplica.

## Testar
- **PSScriptAnalyzer**: `Invoke-ScriptAnalyzer -Path <pasta> -Recurse` (com o arquivo de configuração do projeto, se houver) sem aviso novo; supressão (`[Diagnostics.CodeAnalysis.SuppressMessageAttribute()]`) só com justificativa.
- **Pester** (`Invoke-Pester`) para função com lógica: entrada inválida, caminho feliz, falha de dependência (com `Mock`), e `-WhatIf` não alterando nada. Sem Pester no projeto: rodar os casos à mão e registrar a tabela no card.
- Rodar com `-WhatIf` e `-Verbose` antes do caminho real (operações internas, como temporários, com `-WhatIf:$false` para não poluir a simulação); rodar em cada edição/sistema alvo (5.1 e 7, Windows e Linux) quando o script promete os dois.

## Checklist de revisão
1. Versão e edição alvo declaradas (`#Requires`) e nenhum recurso acima delas.
2. `Set-StrictMode` com versão fixa e `$ErrorActionPreference = 'Stop'`; `$LASTEXITCODE` conferido após cada executável nativo; stderr de nativo não redirecionado sob `Stop` nas versões afetadas.
3. Funções avançadas com parâmetros tipados e validados; quem altera suporta `-WhatIf`/`-Confirm`.
4. Sem aliases nem `Invoke-Expression`; chamadas por splatting; saída em objetos, sem `Write-Host` para dado nem saída acidental.
5. Caminhos com `$PSScriptRoot`/`Join-Path`; codificação explícita e certa para a edição (BOM quando roda no 5.1 com acentos).
6. Nenhum segredo literal, em log ou transcript; nenhuma política de execução afrouxada globalmente.
7. Módulos com `FunctionsToExport` explícito e dependências de versão fixa e fonte confiável.
8. PSScriptAnalyzer sem aviso novo; Pester (ou tabela manual) cobrindo entrada inválida, caminho feliz e `-WhatIf`.
