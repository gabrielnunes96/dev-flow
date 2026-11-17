---
name: docker
description: Convenções para escrever, testar e revisar Dockerfile e Docker Compose no fluxo — build em múltiplos estágios, imagem base fixada e mínima, cache de camadas, usuário não root, .dockerignore, healthcheck, sinais e encerramento, segredos de build, compose para desenvolvimento com bancos e varredura de vulnerabilidades (Trivy). Use ao criar ou revisar Dockerfile, compose.yaml ou a imagem de uma aplicação num projeto com stack docker.
---

# Docker no fluxo

As convenções do **projeto** (registro, nomes de imagem, base corporativa) vencem estas quando conflitarem. Modelos: `../../templates/` (relativo a esta skill).

## Dockerfile
- **Múltiplos estágios**: `build` (SDK, dependências de compilação) → `runtime` (só o necessário para rodar). Modelos por stack em `../../templates/Dockerfile.<stack>`.
- **Base fixada e mínima**: tag de versão explícita (`node:22.11-alpine`, `python:3.12-slim`, `mcr.microsoft.com/dotnet/aspnet:8.0`), idealmente com digest (`@sha256:`). Nunca `latest`. Distroless/chiseled quando a stack permite.
- **Cache de camadas**: copiar primeiro o manifesto de dependências (`package*.json`, `pyproject.toml`+lock, `*.csproj`, `go.mod`/`go.sum`, `pom.xml`), instalar, e só depois copiar o código. `RUN --mount=type=cache` para cache do gerenciador (BuildKit).
- **`.dockerignore`** obrigatório (modelo `../../templates/dockerignore`): `.git`, `node_modules`, `bin/obj`, `.venv`, `.env*`, `.claude/local`, artefatos de teste. O que não está no ignore vai para o contexto (e pode ir para a imagem).
- **Usuário não root**: `USER` numérico (ex.: `10001`) ou o usuário da base (`node`, `app`); arquivos com dono certo (`COPY --chown`).
- **Segredos de build** (token de feed privado): `RUN --mount=type=secret,id=...`, nunca `ARG`/`ENV` com segredo (fica no histórico da imagem).
- **Uma aplicação por container**, processo em primeiro plano, `ENTRYPOINT` em forma JSON (`["dotnet","App.dll"]`) para receber `SIGTERM`; a aplicação encerra com graça. Node/Python atrás de shell → `exec`, ou `--init`/`tini`.
- `HEALTHCHECK` (ou probes do orquestrador) apontando para o healthcheck do perfil (`servico.healthcheck`).
- `EXPOSE` da porta real; configuração por variável de ambiente; logs em stdout/stderr.
- Labels OCI (`org.opencontainers.image.source`, `revision`) quando o pipeline passar os valores.

## Compose (desenvolvimento)
- `compose.yaml` (modelo `../../templates/compose.yaml`) com a aplicação e as dependências (banco, cache, fila) em versões iguais às de produção, volumes nomeados para dados, `healthcheck` nas dependências e `depends_on: condition: service_healthy`.
- Portas de banco publicadas só em `127.0.0.1` (`"127.0.0.1:5432:5432"`). Senhas de dev em `.env` fora do git (com `.env.example` versionado).
- Serve de base para `servico.executar` e para a validação (`validacao.tipo = http`/`sql`) do perfil.

## Testar
- `docker build` (com `--target` de teste, se houver) e `docker run` local subindo o healthcheck: a imagem precisa **rodar**, não só construir.
- Tamanho da imagem (`docker image ls`) comparado ao anterior; crescimento sem motivo é achado.
- Varredura: `trivy image <imagem>` (ou `docker scout cves`) sem vulnerabilidade crítica/alta corrigível; `hadolint Dockerfile` se o projeto usa.

## Checklist de revisão
1. Base com versão fixa (sem `latest`), mínima; multi-stage sem SDK no runtime.
2. Ordem de cópia aproveita cache; `.dockerignore` cobre `.git`, `.env*`, dependências locais.
3. `USER` não root; nenhum segredo em `ARG`/`ENV`/camada.
4. `ENTRYPOINT` em forma JSON; encerramento com `SIGTERM` tratado.
5. Healthcheck presente; porta e variáveis documentadas.
6. Compose: dependências com healthcheck, portas de banco só em localhost, senhas fora do git.
7. Varredura sem crítica/alta corrigível; imagem não cresceu sem motivo.
