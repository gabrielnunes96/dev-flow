---
name: terraform
description: Convenções para escrever, testar e revisar infraestrutura como código com Terraform/OpenTofu no fluxo — estado remoto com lock, módulos e versões fixadas, variáveis tipadas e validadas, ambientes separados, plan revisado antes de apply, recursos protegidos contra destruição, moved/import em vez de recriar, tags, menor privilégio e varredura (tflint, checkov/tfsec). Use ao criar ou revisar arquivos .tf, módulos ou mudanças de infraestrutura em Azure, AWS ou GCP num projeto com stack terraform.
---

# Terraform / OpenTofu no fluxo

As convenções do **projeto** (estrutura de pastas, backend, módulos corporativos, `infra.iac` do perfil) vencem estas quando conflitarem.

Versões com suporte, LTS e mudanças recentes: `../../referencias/atual.md` (veja a data de revisão). Antes de usar API ou recurso, siga o procedimento *projeto primeiro* do fluxo (`referencias/conhecimento.md` do plugin `fluxo`): padrão do projeto → versão em uso → documentação daquela versão → novidade como sugestão.

## Regra de ouro
**A sessão nunca roda `terraform apply`/`destroy`** em ambiente compartilhado. Ela escreve o código, roda `fmt`, `validate`, `plan` (quando há credencial de leitura de dev) e entrega o plano para o usuário ou para o pipeline com aprovação aplicar.

## Escrever
- **Estado remoto com lock** (azurerm storage, S3 + DynamoDB/lockfile, GCS), um estado por ambiente e por domínio (rede, dados, aplicação) — estado gigante é raio de impacto gigante. Nunca estado local versionado.
- **Versões fixadas**: `required_version` e `required_providers` com restrição (`~> 4.10`), `.terraform.lock.hcl` versionado; módulos com `version`/`ref` fixo.
- **Ambientes** por pasta/workspace conforme o projeto (`envs/dev`, `envs/prd`) reutilizando módulos; diferença entre ambientes só em variáveis.
- **Variáveis** com `type`, `description` e `validation` quando há regra; `sensitive = true` para segredo; outputs sensíveis marcados. Segredo nunca em `.tfvars` versionado: vem do cofre (data source do Key Vault/Secrets Manager) ou do pipeline.
- **Nomes e tags** padronizados (`locals` com `tags = { sistema, ambiente, dono, custo }`) aplicados a todo recurso.
- **Proteção**: `lifecycle { prevent_destroy = true }` em banco, storage com dados, chave de criptografia, DNS. Bancos com backup, deleção protegida e retenção.
- **Refatoração sem recriar**: renomear recurso/mover para módulo → bloco `moved`; recurso que já existe → bloco `import` (TF 1.5+). Nunca deixar o plano destruir e recriar o que tem dado.
- **Menor privilégio**: papéis/políticas específicos, sem `*` em ação ou recurso; identidade gerenciada/workload identity em vez de chave.
- **Rede**: nada de banco ou storage com acesso público; regras de entrada mínimas (sem `0.0.0.0/0` em porta de administração); criptografia em repouso e TLS.
- `count`/`for_each`: prefira `for_each` com chave estável (trocar a ordem de uma lista com `count` recria recursos).
- Sem `local-exec`/`null_resource` para o que um provider faz.

## Testar
- `terraform fmt -check -recursive`, `terraform validate`, `tflint` e varredura (`checkov -d .` ou `trivy config .`) verdes.
- `terraform plan -out=plan.tfplan` no ambiente de dev e **ler o plano**: conte `add/change/destroy`; qualquer `destroy`/`replace` (`-/+`) de recurso com dado é bloqueio até explicação. Resumo do plano no card da tarefa.
- Módulos: `terraform test` (TF 1.6+) ou Terratest se o projeto já usa.

## Checklist de revisão
1. Backend remoto com lock; versões de Terraform, providers e módulos fixadas; lock file versionado.
2. Variáveis tipadas, validadas e com `sensitive` onde cabe; nenhum segredo em código ou tfvars.
3. Tags padrão em todos os recursos.
4. `prevent_destroy` em recurso com dado; plano sem destroy/replace inesperado.
5. `moved`/`import` em refatoração; `for_each` com chave estável.
6. Menor privilégio; nada público que não deveria; criptografia e TLS.
7. fmt, validate, tflint e checkov limpos; plano resumido no card.
