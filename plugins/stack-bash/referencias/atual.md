# Conhecimento atual: Bash e sh
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=- -->

> Parte volátil da stack, separada do método (a skill). O Bash não publica ciclos de suporte (não há fonte para a tabela gerada por `scripts/atualizar_conhecimento.py`); esta página é curada pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): o shell e a versão do destino mandam.

## Fontes oficiais
- https://www.gnu.org/software/bash/ (lançamentos e manual)
- https://ftp.gnu.org/gnu/bash/ (versões e patches oficiais)
- https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html (shell POSIX)
- https://github.com/koalaman/shellcheck/releases
- https://github.com/bats-core/bats-core/releases

## Versões
Sem ciclos de suporte publicados: o GNU Bash corrige por patches na versão mais recente, e a versão usada de fato é a do sistema de destino (ver `atual.md` da stack `linux` e a imagem base). Levantado em 2026-11-19 nas fontes acima:

| Item | Situação |
| --- | --- |
| Bash 5.3 | versão mais recente (lançada em 2025-07-30, com patches oficiais) |
| Bash 5.2 | ainda comum em distribuições LTS |
| Bash 3.2 | o `/bin/bash` do macOS (licença): sem arrays associativos, `${var,,}`, `mapfile` |
| `/bin/sh` | dash (Debian/Ubuntu), BusyBox ash (Alpine), Bash em modo POSIX (RHEL): escrever POSIX puro |
| ShellCheck | 0.11.0 |
| bats-core | 1.14.0 |

## O que acompanhar
- Shell e versão do destino: imagem base do container, runner do CI, servidor; `bash --version` antes de usar recurso novo.
- Novas regras do ShellCheck (podem apontar aviso novo em script antigo — tratar como sugestão, não como bloqueio da tarefa).

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
