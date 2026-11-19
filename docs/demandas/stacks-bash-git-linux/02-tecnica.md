# Stacks de Bash, Git e Linux — Especificação técnica

> Demanda: `stacks-bash-git-linux` · 19/11/2026 · Situação: **aprovada em 19/11/2026** (por delegação do usuário nesta sessão)

## 1. Visão da solução
Três plugins de stack seguindo `docs/novo-plugin-de-stack.md`, mais dois ajustes pequenos em `scripts/atualizar_conhecimento.py`: stack sem produto (`produtos=-`) e codinome do ciclo como nome citável.

## 2. Componentes afetados
| Componente | Mudança |
| --- | --- |
| `scripts/atualizar_conhecimento.py` | `produtos=-` → sem bloco de versões e sem consulta; `nomes_do_ciclo` inclui o codinome (1ª palavra, minúscula); `PADROES` para `git`, `ubuntu`, `debian`, `rhel`, `alpine-linux`. |
| `plugins/stack-{bash,git,linux}/` | `.claude-plugin/plugin.json`, `skills/<nome>/SKILL.md`, `referencias/atual.md`; `stack-bash/templates/script.sh`. |
| `plugins/fluxo/schema/projeto.schema.json`, `scripts/perfil.py` | `bash`, `git`, `linux` em `stacks`. |
| `plugins/fluxo/skills/iniciar/SKILL.md` | sinais de detecção. |
| `.claude-plugin/marketplace.json` + `.cursor-plugin` gerado | três entradas. |
| README, manual, `docs/novo-plugin-de-stack.md`, CLAUDE.md | listas de stacks e o `produtos=-`. |

## 3. Contratos
- `atual.md` sem fonte de ciclos: `<!-- dev-flow:conhecimento revisado_em=AAAA-MM-DD produtos=- -->`, seções obrigatórias iguais; `## Versões` em texto livre (sem bloco gerado).
- Detecção (`iniciar`): `*.sh`, `*.bash`, shebang `#!/bin/bash`/`#!/usr/bin/env bash`/`#!/bin/sh` → `bash`; repositório Git (`.git/`) → `git`; unidades systemd, `cloud-init`, Ansible/Packer, scripts de provisionamento de VM, runbooks de servidor → `linux`.

## 4. Dados
Nenhum.

## 5. Integrações externas
endoflife.date (já usada): `git`, `ubuntu`, `debian`, `rhel`, `alpine-linux`.

## 6. Segurança
As skills reforçam: segredo fora de script e do histórico, `chmod` mínimo, SSH sem senha e sem root, nada de `curl | sh` sem verificação, operações destrutivas pelo humano.

## 7. Observabilidade
Não se aplica.

## 8. Estratégia de testes
| CA | Teste |
| --- | --- |
| CA-1 | `tests/test_marketplace.py` (existente, cobre as novas stacks pelo `STACKS`) + `test_perfil`. |
| CA-2, CA-3 | `tests/test_conhecimento.py`: `verificar` e `levantar` com `produtos=-`. |
| CA-4 | `tests/test_conhecimento.py`: varredura com dados falsos de debian/ubuntu/alpine. |
| CA-5 | `sincronizar_hosts.py --check`, `claude plugin validate .`. |
| CA-6 | `tests/test_marketplace.py`: README e manual citam cada `stack-*`. |

## 9. Riscos e decisões
- Padrão de codinome casa palavras comuns (`stretch`)? Limitado a tag de imagem (`imagem:...codinome`) e a 5+ letras; só vira achado se for codinome de ciclo sem suporte.
- `git` em todo projeto carrega a skill em toda tarefa: skill enxuta, focada em decisões e armadilhas.

## 10. Implantação e rollback
Subir versões (`fluxo` 0.4.1, catálogo 0.4.1, stacks novas 0.1.0), sincronizar hosts; rollback = reverter o merge.

## 11. CI/CD
Sem mudança: `azure-pipelines.yml` já roda testes, `--verificar --max-dias 0` e `sincronizar_hosts --check`.
