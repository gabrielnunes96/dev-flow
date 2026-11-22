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

## Modelo de cada especialista
O frontmatter dos especialistas traz `model` por **família** (`haiku`, `sonnet`, `opus`) ou `inherit` (o modelo da sessão), escolhido pela medição da suíte de comportamento (`docs/demandas/modelo-e-documentacao/medicao.md` no repositório do dev-flow): leitura e levantamento num modelo mais barato; decisão estrutural e segurança no modelo da sessão.
- Claude Code: respeita o campo; o apelido aponta para a versão mais nova da família na API da Anthropic (em Bedrock/Vertex/Foundry pode ser uma versão anterior; fixe com `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL` ou `ANTHROPIC_DEFAULT_HAIKU_MODEL`). Para mudar um especialista só: um agente de projeto (`.claude/agents/<nome>.md`) com o mesmo nome tem precedência sobre o do plugin (por isso `.claude/agents/**` pede revisão obrigatória, ex.: CODEOWNERS: quem altera esse arquivo troca o prompt do especialista). `CLAUDE_CODE_SUBAGENT_MODEL` + `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` forçam um modelo em **todos** os especialistas, inclusive `seguranca` e `arquiteto`: é recurso de medição (suíte de comportamento), não configuração do time — nunca force esses dois abaixo do modelo da sessão.
- Cursor e outros hosts: os especialistas do plugin rodam como prompt na sessão ou num subagente do host, no modelo que o host escolher; o campo é ignorado.

## Hooks
- Claude Code: `hooks/hooks.json` (`${CLAUDE_PLUGIN_ROOT}`).
- Cursor (plugin): `hooks/hooks.cursor.json` (`${CURSOR_PLUGIN_ROOT}`).
- Cursor (projeto vendor): rode `python -I scripts/instalar_em_projeto.py --projeto <produto>` (cria `.agents/skills` + `.cursor/hooks.json` com paths relativos ao `_runtime/fluxo`). Alternativa manual: copie `templates/hooks.cursor.json` e defina `DEV_FLOW_FLUXO` para a pasta do plugin `fluxo` exportada.
- Hosts sem hooks: o `guard` não roda sozinho — as skills ainda pedem as mesmas restrições; a garantia automática some.

## Conhecimento atual
Todo especialista e skill de stack segue `conhecimento.md` (projeto primeiro → versão em uso → documentação daquela versão → novidade conforme o perfil). A consulta à documentação usa o que o host tiver (MCP de documentação, busca web) e, na falta, o código dos pacotes instalados. MCPs recomendados por stack e como ligar em cada host: `documentacao.md` (gerador: `scripts/mcp_documentacao.py --host claude|cursor`).

## Perfil
Sempre `.claude/projeto.json` na raiz do projeto consumidor (Cursor com Third-Party Imports também lê `.claude/`).
