---
name: gitlab
description: Cria ou ajusta o .gitlab-ci.yml a partir do perfil do projeto (stages de build, lint, testes, segurança, imagem e deploy por ambiente com aprovação manual) e diagnostica pipelines que falharam com o glab CLI. Use quando o usuário pedir CI/CD no GitLab, .gitlab-ci.yml, ou quando a pipeline de um merge request falhar.
argument-hint: "[criar | ajustar | diagnosticar <pipeline id>]"
---

# GitLab CI/CD

## criar / ajustar
1. Ler o perfil (`stacks`, `comandos`, `ci`, `infra`) e o `.gitlab-ci.yml` existente (e `include:`). Ajustar o existente em vez de criar um paralelo.
2. Partir do modelo `../../templates/gitlab-ci.yml` (relativo a esta skill). Monorepo → `rules: changes:` por pasta, ou pipelines filhas (`trigger: include:`).
3. Regras:
   - `workflow: rules:` para rodar em merge request e na branch base, sem pipeline duplicada (MR + branch).
   - **Mesmos comandos do perfil** (`build`, `teste`, `lint`, `vulnerabilidades`).
   - Imagens de job com versão fixa (`node:22-alpine`, nunca `latest`); `cache:` com `key: files:` do lock; `artifacts: reports: junit:` para testes e `coverage_report` quando houver.
   - Templates de segurança do GitLab (`SAST`, `Secret-Detection`, `Dependency-Scanning`, `Container-Scanning`) quando a licença permitir.
   - Variáveis sensíveis em Settings → CI/CD → Variables, **protegidas e mascaradas**; nada no YAML. Nuvem por OIDC (`id_tokens:`) em vez de chave.
   - Deploy por `environment:` (`dev`, `hml`, `prd` — de `ci.ambientes`); **produção com `when: manual`** e ambiente protegido com aprovadores (configurado na UI; dizer ao usuário).
   - `interruptible: true` em jobs de CI; `timeout` explícito em jobs longos; `needs:` para paralelizar.
4. Validar: `glab ci lint` (ou a API de lint do projeto) e nomes de job únicos. Entregar no commit da tarefa de CI/CD. Criar variáveis, ambientes ou rodar pipeline é ação visível: só com o "sim" do usuário.

## diagnosticar
1. `glab ci list`, `glab ci view <id>`, `glab ci trace <job>` (ou a UI).
2. Classificar: código (reproduzir local com o comando do perfil), teste instável, runner (tag, imagem, cache), variável ausente ou protegida não disponível na branch.
3. Corrigir o que é do código num commit novo; configuração do GitLab → dizer ao usuário o que mudar. `glab ci retry` só com o "sim".
