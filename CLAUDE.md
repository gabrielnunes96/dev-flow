# CLAUDE.md

Este repositório é o marketplace `dev-flow`: plugins do Claude Code com o fluxo de desenvolvimento do time. Ele se desenvolve pelo próprio fluxo (perfil em `.claude/projeto.json`).

## Estrutura
- `.claude-plugin/marketplace.json` lista os plugins de `plugins/` (**fonte canônica**).
- `.cursor-plugin/marketplace.json` e `plugins/*/.cursor-plugin/plugin.json` são **gerados** por `python -I scripts/sincronizar_hosts.py` (não editar à mão).
- `scripts/exportar_skills.py`: vendor de plugins/skills para um projeto (Agent Skills / Cloud Agents).
- `scripts/atualizar_conhecimento.py`: levantamento de versões das stacks (endoflife.date) → tabelas de `plugins/stack-*/referencias/atual.md` e relatório; `--verificar` sem rede. `scripts/avaliar_agentes.py`: suíte de comportamento (`plugins/*/evals/`) com qualquer CLI de agente. Revisão periódica: skill `.claude/skills/atualizar-conhecimento` + `azure-pipelines-conhecimento.yml` / `.github/workflows/conhecimento.yml`.
- `scripts/instalar_em_projeto.py`: instala no produto (`.agents/skills` + hooks Cursor); `--azure` inclui Boards e Pipelines.
- `plugins/fluxo`: núcleo (skills, agentes, hooks, scripts, modelos, schema do perfil). Os demais são adaptadores de rastreador e CI (`azure-*`, `github-actions`, `gitlab-ci`), stacks (`stack-*`: linguagens, shell (Bash e PowerShell), bancos, infraestrutura, Git e Linux) e extras (`design`, `video`, `logs`).
- `tests/`: unittest dos scripts, hooks e da consistência do marketplace (`test_marketplace.py`, `test_portabilidade.py`).
- `docs/manual/index.html`: manual navegável (abre direto no navegador); atualizar junto com o README ao mudar skills, agentes ou plugins.
- `exemplos/`: perfis reais; o teste valida todos.

## Convenções
- Tudo em pt-BR. Skills: frontmatter `name`, `description` (o que faz + quando usar), `argument-hint` quando recebe argumento.
- **Nada específico de projeto dentro de skill**: comando, caminho, id de rastreador, porta → `projeto.json`. Se uma skill precisar de um dado novo, adicione ao schema, a `perfil.py validar` e a um teste.
- Scripts: só biblioteca padrão do Python (rodam com `python -I` em qualquer máquina), importam vizinhos com `sys.path.insert` (o `-I` não inclui a pasta do script), não imprimem segredos, código de saída significativo. Exceção: o motor do plugin `video` (`render.py`) usa Pillow, numpy e imageio-ffmpeg (`plugins/video/requirements.txt`); a parte testada (`roteiro.py`) segue só com a biblioteca padrão.
- Hooks: forçar UTF-8 em stdin/stdout/stderr (no Windows o padrão é cp1252 e o Claude Code lê UTF-8). Falha ao ler perfil não bloqueia.
- **Conhecimento volátil fora do método**: versão, LTS, fim de suporte e novidade de tecnologia vão em `plugins/stack-*/referencias/atual.md` (com data e fonte), não no texto da skill ou do agente; exemplos de versão nas skills ficam neutros (`<versão do projeto>`). Especialista novo leva o bloco "Conhecimento atual (projeto primeiro)" e, se possível, casos em `plugins/<plugin>/evals/<agente>/`.
- Caminhos entre skill e scripts: relativos ao diretório da skill (`../../scripts/`); o hook de contexto imprime o caminho absoluto.
- Mudança de comportamento de script/hook → teste em `tests/`.

## Comandos
```bash
python -I scripts/sincronizar_hosts.py
python -I scripts/sincronizar_hosts.py --check
python -m unittest discover -s tests
claude plugin validate .
```
Versão: subir `version` no `plugin.json` alterado e no `marketplace.json` ao publicar mudança; depois rodar `sincronizar_hosts.py`.
