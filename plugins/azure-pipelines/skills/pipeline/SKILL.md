---
name: pipeline
description: Cria ou ajusta pipelines YAML do Azure DevOps a partir do perfil do projeto (build, testes, verificação de pacotes vulneráveis, publicação de artefato, deploy por ambiente com aprovação) e diagnostica execuções que falharam. Use quando o usuário pedir CI/CD, pipeline, YAML do Azure DevOps, ou quando a pipeline de um PR falhar.
argument-hint: "[criar | ajustar | diagnosticar <run id>]"
---

# Azure Pipelines

## criar / ajustar
1. Ler o perfil (`stacks`, `comandos`) e o que já existe (`azure-pipelines.yml`, `.azure-pipelines/`, `Dockerfile`). Ajustar o existente em vez de criar um paralelo.
2. Partir dos modelos em `../../templates/` (relativo a esta skill): `dotnet.yml`, `front.yml`, `sql.yml` e `deploy-estagios.yml`. Monorepo → um pipeline por componente com `trigger.paths.include` da pasta dele.
3. Regras:
   - CI em PR e na branch base; CD só na branch base.
   - Mesmos comandos do perfil (`build`, `teste`, `lint`, `vulnerabilidades`), para o que passa local passar no CI.
   - Testes publicam resultado (`PublishTestResults`/`dotnet test --logger trx`) e cobertura quando houver.
   - Segredos só em variable groups / Key Vault, referenciados por nome; nada no YAML.
   - Deploy por `environment` (`dev`, `hml`, `prd`), e **produção com aprovação manual** configurada no environment (dizer ao usuário que a aprovação é configurada na UI do environment; não fica no YAML).
   - Versões de tarefas fixadas (`UseDotNet@2` com `version`, `NodeTool@0` com `versionSpec`).
4. Validar a sintaxe localmente o quanto der (YAML válido, nomes de stage/job únicos) e entregar no commit da tarefa de CI/CD. Criar a pipeline no Azure DevOps (`az pipelines create`) é ação visível para o time: só com o "sim" do usuário.

## diagnosticar
1. `az pipelines runs show --id <run>` e `az pipelines runs artifact list`/logs do job que falhou (ou a UI pelo navegador, se o usuário preferir).
2. Classificar: erro de código (reproduzir local com o mesmo comando do perfil), teste instável, ambiente/agente (versão do SDK, cache, permissão), segredo/variável ausente.
3. Corrigir o que é do código num commit novo; o que é de configuração do Azure (variable group, permissão, environment) → dizer ao usuário exatamente o que mudar, sem mudar sozinho.
