## Stacks de Bash, PowerShell, Git e Linux

Quatro plugins de stack novos no formato das outras: skill (implementar → testar → checklist) e `referencias/atual.md`. Funcionam em qualquer host (Claude Code, Cursor, Agent Skills).

> Esta branch parte de `conhecimento-atualizavel` (formato `atual.md`): fazer merge daquela antes, ou junto.

### O que muda
| Tarefa | O que muda para o consumidor | Commit |
| --- | --- | --- |
| T1 | Levantamento de conhecimento aceita stack sem ciclo de suporte (`produtos=-`) e reconhece distribuição citada por codinome em tag de imagem, por tag de versão e por runner de CI (`debian:buster-slim`, `aspnet:6.0-focal`, `ubuntu-20.04`, `alpine3.18`, `ubi7`). | `25eb762` |
| T2 | `stack-bash`: modo estrito e suas armadilhas, aspas, arrays, `trap` + `mktemp`, `getopts`, portabilidade, segredos, ShellCheck e bats; modelo `templates/script.sh`. | `a25c54a` |
| T3, T4 | `stack-git`: commits atômicos, conflitos, histórico publicado intocável, operações destrutivas só pelo humano, `.gitattributes`, segredos, LFS, bisect/reflog. `stack-linux`: systemd endurecido, permissões, SSH, firewall, journald, timers; mudança em servidor pelo humano. Tabelas de Git, Ubuntu, Debian, RHEL e Alpine geradas. | `414ae19` |
| T5 | Stacks `bash`, `git` e `linux` no perfil, no schema e na detecção do `iniciar`; README, manual, catálogo dos dois hosts; `fluxo` 0.4.1, stacks novas 0.1.0. | `44858d2` |
| T6 | `stack-powershell` (pedido depois): PowerShell 7 e 5.1, modo estrito, `$LASTEXITCODE`, `-WhatIf`, codificação e BOM, segredos, PSScriptAnalyzer e Pester; modelo `templates/script.ps1`; tabela do `powershell`; `fluxo` 0.4.2. | `e6fb8e0` |
| — | Correções da revisão (regex, operações destrutivas do Git, `zdiff3`, `set -e`, `-h` do modelo, `LoadCredential`, testes). | `b32180f` |

### Impacto em consumidores
- Nada quebra: stacks novas são opcionais. Para usar, instale o plugin e acrescente a stack em `stacks` do perfil.

### Como foi validado
- 124 testes passando (stacks bash, git, linux e powershell); `claude plugin validate . --strict`; `sincronizar_hosts.py --check`; `atualizar_conhecimento.py --verificar` e levantamento real sem achados.
- Modelo de script executado (ajuda, uso errado, entrada inexistente, simulação). ShellCheck e bats não estavam instalados: não rodados.
- Revisão pelo especialista revisor; achados corrigidos em `b32180f`. Sem passada formal do especialista de segurança.

### Implantação
- Merge (depois de `conhecimento-atualizavel`) e `claude plugin marketplace update dev-flow` (Cursor: refresh do Team Marketplace). Rollback = reverter o merge.

Especificações: `docs/demandas/stacks-bash-git-linux/`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
