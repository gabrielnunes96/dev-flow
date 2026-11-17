---
name: actions
description: Cria ou ajusta workflows do GitHub Actions a partir do perfil do projeto (CI com build, lint, testes e vulnerabilidades; imagem Docker publicada no registro; deploy por ambiente com aprovação) e diagnostica execuções que falharam com o gh CLI. Use quando o usuário pedir CI/CD no GitHub, workflow, GitHub Actions, ou quando a verificação de um PR no GitHub falhar.
argument-hint: "[criar | ajustar | diagnosticar <run id>]"
---

# GitHub Actions

## criar / ajustar
1. Ler o perfil (`stacks`, `comandos`, `ci`, `infra`) e o que já existe em `.github/workflows/`. Ajustar o existente em vez de criar um paralelo.
2. Partir dos modelos em `../../templates/` (relativo a esta skill): `ci.yml` (matriz por stack, com os comandos do perfil), `docker.yml` (build e publicação de imagem) e `deploy.yml` (ambientes em sequência). Monorepo → um workflow por componente com `paths:` da pasta dele.
3. Regras:
   - CI em `pull_request` e `push` na branch base; deploy só na branch base (ou tag de versão).
   - **Mesmos comandos do perfil** (`build`, `teste`, `lint`, `vulnerabilidades`), para o que passa local passar no CI.
   - `permissions:` mínimas no topo (`contents: read`) e ampliadas só no job que precisa (`packages: write`, `id-token: write` para OIDC).
   - **Ações fixadas por SHA** de commit (com a versão em comentário) — tag pode ser movida. Dependabot para mantê-las atualizadas.
   - Segredos em `secrets`/`vars` do repositório ou do **environment**; nada no YAML. Nuvem por **OIDC** (`azure/login`, `aws-actions/configure-aws-credentials`, `google-github-actions/auth`) em vez de chave de longa duração.
   - Cache do gerenciador (`actions/setup-*` com `cache:`), `concurrency` para cancelar execuções antigas do mesmo PR, `timeout-minutes` em todo job.
   - Resultados de teste e cobertura como artefato ou resumo (`$GITHUB_STEP_SUMMARY`).
   - Deploy por `environment:` (`dev`, `hml`, `prd` — de `ci.ambientes`); **produção com revisores obrigatórios**, configurados em Settings → Environments (dizer ao usuário; não fica no YAML).
   - Nunca `pull_request_target` com checkout do código do PR; nunca interpolar `${{ github.event.* }}` direto em `run:` (injeção) — passe por `env:`.
4. Validar localmente o quanto der: YAML válido, `actionlint` se disponível, nomes de job únicos. Entregar no commit da tarefa de CI/CD. Criar secrets, environments ou disparar workflow é ação visível para o time: só com o "sim" do usuário.

## diagnosticar
1. `gh run list --branch <branch> -L 5`, `gh run view <id> --log-failed` (ou `gh pr checks <pr>`).
2. Classificar: erro de código (reproduzir local com o mesmo comando do perfil), teste instável, ambiente do runner (versão de SDK, cache corrompido, imagem do runner atualizada), permissão/`permissions:` insuficiente, segredo ou variável ausente.
3. Corrigir o que é do código num commit novo; o que é configuração do GitHub (secret, environment, proteção de branch) → dizer ao usuário exatamente o que mudar, sem mudar sozinho. Reexecutar (`gh run rerun --failed`) só com o "sim".
