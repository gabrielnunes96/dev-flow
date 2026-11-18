# Hosts: Claude Code, Cursor e outros agentes

O processo é o mesmo. Muda só como o host carrega skills, agentes e hooks.

## Invocar uma skill
- Claude Code: `/fluxo:<nome>` (ex.: `/fluxo:iniciar`) ou pedido em linguagem natural.
- Cursor / Agent Skills: `/<nome>` (ex.: `/iniciar`) ou pedido em linguagem natural (“iniciar o fluxo”, “próxima task”).
- Qualquer host: descreva a etapa; a `description` do `SKILL.md` é o gatilho.

## Perguntar ao usuário
Se o host tiver ferramenta de pergunta estruturada (ex.: AskUserQuestion no Claude), use. Senão, pergunte no chat — no máximo 4 perguntas por rodada, com opções e uma recomendação.

## Especialistas (agentes)
Arquivos em `../../agents/<especialista>.md` (relativo à skill). Dispare um subagente / Task / sessão isolada com esse prompt. Nomes: `analista`, `arquiteto`, `revisor`, `seguranca`, `testador`, `depurador`, `validador`. Sem harness de subagente → leia o arquivo e execute o papel na sessão atual, devolvendo o mesmo formato de resumo.

## Hooks
- Claude Code: `hooks/hooks.json` (`${CLAUDE_PLUGIN_ROOT}`).
- Cursor (plugin): `hooks/hooks.cursor.json` (`${CURSOR_PLUGIN_ROOT}`).
- Cursor (projeto vendor): rode `python -I scripts/instalar_em_projeto.py --projeto <produto>` (cria `.agents/skills` + `.cursor/hooks.json` com paths relativos ao `_runtime/fluxo`). Alternativa manual: copie `templates/hooks.cursor.json` e defina `DEV_FLOW_FLUXO` para a pasta do plugin `fluxo` exportada.
- Hosts sem hooks: o `guard` não roda sozinho — as skills ainda pedem as mesmas restrições; a garantia automática some.

## Perfil
Sempre `.claude/projeto.json` na raiz do projeto consumidor (Cursor com Third-Party Imports também lê `.claude/`).
