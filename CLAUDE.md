# CLAUDE.md

Este repositório é o marketplace `dev-flow`: plugins do Claude Code com o fluxo de desenvolvimento do time. Ele se desenvolve pelo próprio fluxo (perfil em `.claude/projeto.json`).

## Estrutura
- `.claude-plugin/marketplace.json` lista os plugins de `plugins/`.
- `plugins/fluxo`: núcleo (skills, agentes, hooks, scripts, modelos, schema do perfil). Os demais plugins são adaptadores (`azure-*`) e stacks (`stack-*`).
- `tests/`: unittest dos scripts e hooks (`apoio.py` cria projetos temporários com perfil).
- `exemplos/`: perfis reais; o teste valida todos.

## Convenções
- Tudo em pt-BR. Skills: frontmatter `name`, `description` (o que faz + quando usar), `argument-hint` quando recebe argumento.
- **Nada específico de projeto dentro de skill**: comando, caminho, id de rastreador, porta → `projeto.json`. Se uma skill precisar de um dado novo, adicione ao schema, a `perfil.py validar` e a um teste.
- Scripts: só biblioteca padrão do Python (rodam com `python -I` em qualquer máquina), importam vizinhos com `sys.path.insert` (o `-I` não inclui a pasta do script), não imprimem segredos, código de saída significativo. Exceção: o motor do plugin `video` (`render.py`) usa Pillow, numpy e imageio-ffmpeg (`plugins/video/requirements.txt`); a parte testada (`roteiro.py`) segue só com a biblioteca padrão.
- Hooks: forçar UTF-8 em stdin/stdout/stderr (no Windows o padrão é cp1252 e o Claude Code lê UTF-8). Falha ao ler perfil não bloqueia.
- Caminhos entre skill e scripts: relativos ao diretório da skill (`../../scripts/`); o hook de contexto imprime o caminho absoluto.
- Mudança de comportamento de script/hook → teste em `tests/`.

## Comandos
```bash
python -m unittest discover -s tests
claude plugin validate .
```
Versão: subir `version` no `plugin.json` alterado e no `marketplace.json` ao publicar mudança.
