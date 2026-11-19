# Stacks de Bash, Git e Linux — Especificação funcional

> Demanda: `stacks-bash-git-linux` · Versão 1 · 19/11/2026 · Situação: **aprovada em 19/11/2026** (por delegação do usuário nesta sessão)

## 1. Objetivo
Dar aos especialistas e ao ciclo da tarefa as convenções de três assuntos que aparecem em quase todo projeto e hoje não têm skill: scripts de shell (Bash/sh), uso do Git e administração de servidores Linux.

## 2. Contexto
- O fluxo carrega a skill `stack-X:X` para cada stack do perfil (`fluxo:task`, passo 4) e o revisor usa o "Checklist de revisão" dela.
- Scripts de shell existem em quase todo repositório (entrypoint de container, CI, deploy, utilitários) e são fonte comum de defeito (aspas, `set -e`, portabilidade).
- O Git é usado por todo projeto; o perfil já define a política (`git.push`, `formato_commit`), mas não há método para histórico, conflitos, `.gitattributes`, segredos e reescrita de histórico.
- Linux aparece em servidores, VMs, imagens base e runners de CI: systemd, permissões, pacotes, SSH, logs.

## 3. Atores
- Especialistas do `fluxo` (revisor, segurança, testador, depurador) e a sessão que implementa a tarefa.
- Mantenedor do dev-flow (revisão periódica do conhecimento).

## 4. Escopo
**Dentro**: plugins `stack-bash`, `stack-git` e `stack-linux` no formato das outras stacks (skill com implementar → testar → checklist; `referencias/atual.md`); stacks `bash`, `git` e `linux` no perfil, na detecção da skill `iniciar`, no README, no manual e no catálogo dos dois hosts.
**Fora**: PowerShell, zsh/fish, administração de Windows Server, gestão de configuração (Ansible), Git hosting (PR/review ficam nos adaptadores de CI).

## 5. Regras de negócio
- RN-1: o perfil e as convenções do projeto vencem a skill; a política de Git do perfil (`git.*`) vence a skill `git`.
- RN-2: nada específico de projeto nas skills; versões só no `atual.md`.
- RN-3: nenhuma skill manda a sessão fazer operação destrutiva sozinha (`push --force` em branch compartilhada, reescrever histórico publicado, `rm -rf` com variável, mudar servidor de produção): ela prepara e o humano executa.
- RN-4: funciona em qualquer host (Claude Code, Cursor, Agent Skills).

## 6. Requisitos funcionais
- RF-1: `stack-bash`: escrever scripts robustos (modo estrito, aspas, `trap`, `mktemp`, portabilidade sh × bash), testar com ShellCheck/shfmt/bats, checklist.
- RF-2: `stack-git`: commits e branches, conflitos, rebase × merge, `.gitattributes` (fim de linha), `.gitignore`, segredos no histórico, LFS, hooks, operações que pedem o humano; checklist.
- RF-3: `stack-linux`: systemd, usuários e permissões, pacotes e atualizações, SSH, firewall, logs (journald), sistema de arquivos e cron/timers, diagnóstico; checklist.
- RF-4: cada stack tem `referencias/atual.md`; Git e Linux com tabela gerada (endoflife.date: `git`; `ubuntu`, `debian`, `rhel`, `alpine-linux`); Bash sem ciclo de suporte publicado declara isso e continua sujeito à revisão periódica.
- RF-5: o levantamento reconhece citações de distribuição por codinome (`bookworm`, `jammy`) e por tag de imagem/runner (`ubuntu-22.04`, `alpine3.18`, `ubi8`).
- RF-6: `iniciar` detecta as três stacks.

## 7. Requisitos não funcionais
- Scripts só com a biblioteca padrão; testes em `tests/`.

## 8. Critérios de aceite
- CA-1: as três stacks estão em `perfil.STACKS` e no schema; `test_marketplace` confere plugin, seções e checklist (≥ 5 itens).
- CA-2: `atualizar_conhecimento.py --verificar` aceita `produtos=-` (sem fonte de ciclos) sem exigir bloco de versões, e o modo online não consulta a rede para essa stack, mas aponta revisão vencida.
- CA-3: `--verificar` continua exigindo produtos e bloco para quem não declarou `-`.
- CA-4: uma citação `debian:buster-slim`, `ubuntu-20.04` ou `node:20-alpine3.18` de ciclo sem suporte vira achado `versao_sem_suporte`; `align-items: stretch` não.
- CA-5: catálogo Claude e Cursor sincronizados; `claude plugin validate .` ok.
- CA-6: README e manual listam as três stacks.

## 9. Impacto em consumidores
Nenhuma quebra: stacks novas são opcionais. Quem quiser instala o plugin e acrescenta a stack ao perfil.

## 10. Dúvidas em aberto
- PowerShell como stack própria (equipe usa Windows): proposta para depois.
