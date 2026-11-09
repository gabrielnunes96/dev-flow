# Migração da Acme.API.Ponte para o plugin

A Ponte é o projeto piloto: tudo o que o `.claude/` local dela fazia tem equivalente no plugin, e o perfil já está em `.claude/projeto.json` (cópia em [`exemplos/ponte/projeto.json`](../exemplos/ponte/projeto.json)).

## Equivalência

| Local da Ponte (`.claude/`) | Plugin |
| --- | --- |
| `skills/proxima-task` | `fluxo:task` (lê Boards/estados/validação do perfil) |
| `skills/status-pbi` | `fluxo:status` |
| `skills/proxima-task/scripts/token.py` | `fluxo/scripts/token_login.py` (mesmo pinning; config em `validacao.token`) |
| `skills/proxima-task/scripts/api.py` | `fluxo/scripts/servico.py` (seção `servico`) |
| `skills/proxima-task/scripts/chamar.py` | `fluxo/scripts/http_lote.py` (+ `esperado`, máscara e tabela do card) |
| `agents/revisor-ponte` | `fluxo:revisor` + checklist `stack-dotnet` + `CLAUDE.md`/`rules` do projeto |
| `agents/sandbox-runner` | `fluxo:validador` (tipo `http`) |
| `hooks/guard.py` | `fluxo/hooks/guard.py` com `protecao` do perfil (equivalência coberta em `tests/test_guard.py`) |
| `rules/boards-e-tasks.md` | `rastreador` do perfil + skill `azure-boards:boards` |
| `rules/git-e-seguranca.md` | `git` e `protecao` do perfil |
| `rules/sandbox-provedora.md` | continua no projeto (`validacao.dados`) |
| `CLAUDE.md` | continua no projeto (fatos da Ponte) |

Validado em 27/10/2026 na Ponte real: `servico.py subir --build` (build + healthcheck), `http_lote.py` com status esperado, `servico.py derrubar`. `token_login.py` respondeu código 2 (sem VPN), como o original.

## Passos

1. Instalar: `claude plugin marketplace add C:/caminho/para/dev-flow` e `claude plugin install fluxo@dev-flow`, `stack-dotnet@dev-flow`, `azure-boards@dev-flow`.
2. Abrir uma sessão na Ponte: o hook de contexto deve mostrar "Projeto Acme.API.Ponte (dotnet)".
3. Desligar o guard local para não rodar dois guards: remover o bloco `hooks` de `.claude/settings.local.json` da Ponte (é você quem altera configuração de permissão/hook).
4. Permissões: trocar em `settings.local.json` os `python -I .claude/skills/proxima-task/scripts/...` pelos scripts do plugin (`python -I <caminho do plugin>/scripts/*.py`); o caminho de instalação aparece no hook de contexto.
5. Usar `/fluxo:task` na próxima tarefa do PBI 1001 (ex.: a 1003, quando você liberar). Funcionou → apagar `skills/`, `agents/` e `hooks/` locais; manter `rules/sandbox-provedora.md`, `local/` e `projeto.json`.

As tarefas do 1001 vivem no Boards; para usar a fila local, `fluxo:boards ler` pode gerar `tarefas.json` em `.claude/local/demandas/pbi-1001/` a partir dos filhos do PBI.
