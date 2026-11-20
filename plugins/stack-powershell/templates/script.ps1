#Requires -Version 5.1
<#
.SYNOPSIS
    <O que este script faz, em uma linha.>
.EXAMPLE
    ./script.ps1 -Entrada ./dados.csv -WhatIf
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string] $Entrada
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Entrada)) {
    throw "não encontrado: $Entrada"
}
$Entrada = Convert-Path -LiteralPath $Entrada  # caminho absoluto: métodos .NET usam outro diretório atual

$temp = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName())
$null = New-Item -ItemType Directory -Path $temp -WhatIf:$false -Confirm:$false
try {
    if ($PSCmdlet.ShouldProcess($Entrada, 'Processar')) {
        Write-Verbose "processando $Entrada"
        # ... trabalho aqui; após executável nativo: if ($LASTEXITCODE -ne 0) { throw "falhou: $LASTEXITCODE" }
        [pscustomobject]@{ Entrada = $Entrada; Situacao = 'ok' }
    }
}
finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue -WhatIf:$false -Confirm:$false
}
