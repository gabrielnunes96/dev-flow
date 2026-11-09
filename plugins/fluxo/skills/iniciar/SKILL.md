---
name: iniciar
description: Prepara um projeto para o fluxo — detecta stack e comandos, cria .claude/projeto.json (perfil), um CLAUDE.md enxuto se não houver, a pasta de especificações e as permissões dos comandos seguros. Use quando o usuário quiser usar o fluxo num projeto novo, "configurar o plugin aqui" ou quando o hook avisar que falta o perfil.
argument-hint: "[caminho do projeto]"
---

# Iniciar um projeto no fluxo

## 1. Detectar (sem perguntar o que dá para ler)
- Stack pelos arquivos: `*.sln`/`*.csproj` → dotnet; `package.json` → front/node (front se houver React/Angular/Vue/Vite); `*.sql`/`*.sqlproj`/migrations → sql; `pyproject.toml` → python. Vários → todos.
- Comandos: scripts do `package.json`, solução e projetos de teste .NET, `Makefile`, pipelines existentes (`azure-pipelines.yml`), `launchSettings.json` (perfis, portas, healthcheck).
- Git: branch padrão (`git symbolic-ref refs/remotes/origin/HEAD` ou `main`/`master`), o que já está em `.gitignore`/`.git/info/exclude`.
- Código gerado (pastas `Connected Services`, SDK gerado por OpenAPI, migrations geradas) → candidatos a `protecao.gerados`.

## 2. Perguntar só o que é do usuário (AskUserQuestion, até 4)
- Rastreador: local ou Azure Boards (org/projeto/item raiz).
- Onde ficam as especificações: versionadas em `docs/demandas` (recomendado) ou locais em `.claude/local/demandas`.
- Ambiente de validação: URL, se exige token/VPN, onde ficam os dados de teste.
- O que não pode ser tocado (diretórios, sistemas).

## 3. Gravar
- `.claude/projeto.json` a partir de `../../templates/projeto.json`, com `$schema` apontando para `../../schema/projeto.schema.json` (caminho absoluto). `python -I ../../scripts/perfil.py validar` até "perfil ok".
- `CLAUDE.md`: se não existir, pelo modelo `../../templates/CLAUDE.md`, só com fatos detectados (arquitetura real, comandos). Se existir, não reescrever; sugerir o que mover para o perfil.
- Segredos locais (token, usuário de login) só em `.claude/local/`, que deve estar no `.gitignore` ou no `.git/info/exclude`.
- Permissões: propor ao usuário a lista `permissions.allow` com os comandos do perfil e os scripts do plugin, e `deny` para `git push` quando `git.push = humano`. Mostrar o JSON e deixar o usuário aplicar em `.claude/settings.local.json` (não escrever configuração de permissão sozinho).

## 4. Fechar
- Resumo do perfil (`perfil.py mostrar`) e próximos passos: `/fluxo:demanda` para começar ou `/fluxo:entregar` para o fluxo completo.
