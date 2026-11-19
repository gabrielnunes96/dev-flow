---
name: iniciar
description: Prepara um projeto para o fluxo — detecta stack e comandos, cria .claude/projeto.json (perfil), um CLAUDE.md enxuto se não houver, a pasta de especificações e as permissões dos comandos seguros. Use quando o usuário quiser usar o fluxo num projeto novo, "configurar o plugin aqui" ou quando o hook avisar que falta o perfil.
argument-hint: "[caminho do projeto]"
---

# Iniciar um projeto no fluxo

## 1. Detectar (sem perguntar o que dá para ler)
- Stack pelos arquivos (vários → todos):
  | Sinal | Stack |
  | --- | --- |
  | `*.sln`, `*.csproj` | dotnet |
  | `package.json` com React/Angular/Vue/Vite/Next/Svelte | front |
  | `package.json` com Express/Fastify/Nest/Koa, ou sem framework de UI | node |
  | `pyproject.toml`, `requirements.txt`, `setup.py` | python |
  | `pom.xml`, `build.gradle(.kts)` | java |
  | `go.mod` | go |
  | `*.sql`, `*.sqlproj` com SQL Server (`sqlcmd`, `NVARCHAR`, `GO`) | sql |
  | dependência/conexão Postgres (`psycopg`, `pg`, `Npgsql`, `postgresql://`, Flyway/Liquibase/Alembic com Postgres) | postgres |
  | dependência/conexão MySQL/MariaDB (`mysql2`, `PyMySQL`, `MySqlConnector`, `mysql://`) | mysql |
  | `mongoose`, `pymongo`, `MongoDB.Driver`, `mongodb://` | mongodb |
  | `redis`, `ioredis`, `StackExchange.Redis`, `redis://` | redis |
  | `Dockerfile`, `compose.yaml`/`docker-compose.yml` | docker |
  | manifestos com `apiVersion:`/`kind:`, `Chart.yaml`, `kustomization.yaml` | kubernetes |
  | `*.tf`, `.terraform.lock.hcl` | terraform |
- Comandos: scripts do `package.json`, solução e projetos de teste .NET, `Makefile`/`justfile`/`Taskfile.yml`, `pyproject.toml` (pytest, ruff, mypy), `pom.xml`/`gradlew`, `go.mod` (`go test ./...`, `go vet`), pipelines existentes, `launchSettings.json` (perfis, portas, healthcheck), `compose.yaml` (serviços e portas). A skill da stack lista os comandos típicos.
- CI → `ci.provedor`: `azure-pipelines.yml`/`.azure-pipelines/` → azure-pipelines; `.github/workflows/` → github-actions; `.gitlab-ci.yml` → gitlab-ci. Nenhum → perguntar junto com o rastreador.
- Infra → `infra`: nuvem pelos provedores do Terraform/SDKs (`azurerm`, `aws`, `google`), orquestrador (`kubernetes`, `compose`, app service, serverless), ambientes que aparecem em pipelines/manifestos (`dev`, `hml`, `prd`).
- Git: branch padrão (`git symbolic-ref refs/remotes/origin/HEAD` ou `main`/`master`), o que já está em `.gitignore`/`.git/info/exclude`.
- Código gerado (pastas `Connected Services`, SDK gerado por OpenAPI, migrations geradas) → candidatos a `protecao.gerados`.

## 2. Perguntar só o que é do usuário (até 4)
Use a ferramenta de pergunta do host se existir; senão, pergunte no chat — opções + uma recomendação.
- Rastreador: local ou Azure Boards (org/projeto/item raiz).
- Onde ficam as especificações: versionadas em `docs/demandas` (recomendado) ou locais em `.claude/local/demandas`.
- Ambiente de validação: URL, se exige token/VPN, onde ficam os dados de teste.
- O que não pode ser tocado (diretórios, sistemas).
- Novidades de tecnologia (`conhecimento.novidades`): projeto novo → recomendar `aplicar`; projeto existente → `sugerir` (padrão; pode omitir). Ver `../../referencias/conhecimento.md`.

## 3. Gravar
- `.claude/projeto.json` a partir de `../../templates/projeto.json`, com `$schema` apontando para `../../schema/projeto.schema.json` (caminho absoluto). `python -I ../../scripts/perfil.py validar` até "perfil ok".
- `CLAUDE.md`: se não existir, pelo modelo `../../templates/CLAUDE.md`, só com fatos detectados (arquitetura real, comandos). Se existir, não reescrever; sugerir o que mover para o perfil.
- Segredos locais (token, usuário de login) só em `.claude/local/`, que deve estar no `.gitignore` ou no `.git/info/exclude`.
- Permissões: propor ao usuário a lista `permissions.allow` com os comandos do perfil e os scripts do plugin, e `deny` para `git push` quando `git.push = humano`. Mostrar o JSON e deixar o usuário aplicar nas settings locais do host (Claude: `.claude/settings.local.json`; Cursor: equivalente de allowlist). Não escrever configuração de permissão sozinho.
- Hooks (opcional): no Cursor, se o plugin não trouxe hooks, oferecer `../../templates/hooks.cursor.json` → `.cursor/hooks.json` com `DEV_FLOW_FLUXO` apontando para este plugin. Detalhes em `../../referencias/hosts.md`.

## 4. Fechar
- Resumo do perfil (`perfil.py mostrar`) e próximos passos: skill `demanda` / `/fluxo:demanda` / “escrever a funcional”, ou skill `entregar` para o fluxo completo.
