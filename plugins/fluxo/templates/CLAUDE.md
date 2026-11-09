# CLAUDE.md

Fatos do projeto que valem em toda conversa. Processo (como especificar, planejar, implementar, validar) fica no plugin `fluxo`; comandos, rastreador e proteções ficam em `.claude/projeto.json`. Mantenha este arquivo curto: tudo aqui custa contexto em toda mensagem.

## Contexto e limites
- O que é o projeto, quem consome, de onde veio.
- O que não tocar (diretórios, sistemas) — e declare também em `protecao` no perfil para o guard bloquear.

## Arquitetura
| Pasta | Projeto | Papel |
| --- | --- | --- |
| | | |

Fluxo de uma requisição/processo: `A -> B -> C`.

## Convenções
- Nomes, rotas, idioma, padrões de erro, padrão para adicionar uma operação.

## Armadilhas conhecidas
- Comportamentos não óbvios que já custaram tempo.
