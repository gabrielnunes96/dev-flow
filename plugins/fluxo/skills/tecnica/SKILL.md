---
name: tecnica
description: Escreve a especificação técnica (02-tecnica.md) de uma demanda a partir da funcional aprovada e do código real dos repositórios afetados — componentes, contratos, dados, integrações, segurança, estratégia de testes por critério de aceite, riscos, implantação e CI/CD. Use quando o usuário pedir a "técnica", o desenho da solução ou a análise de impacto de uma demanda.
argument-hint: "[slug da demanda]"
---

# Funcional → especificação técnica

## 1. Pré-condições
- `{docs}/{slug}/01-funcional.md` existe e está **aprovada** (topo). Não aprovada → parar e dizer o que falta.
- Perfil e convenções (`convencoes` do perfil) lidos. Para cada stack, carregar a skill da stack.

## 2. Levantar o impacto no código real
- Delegar ao subagente `fluxo:analista` (um por repositório quando forem vários, em paralelo): requisitos e critérios da funcional + pergunta "onde e como isso entra no código existente". Ele devolve arquivos-chave com linha, padrões a seguir, contratos atuais e riscos.
- Repositório fora da sessão → pedir o caminho ao usuário (não adivinhar).
- Em paralelo com o analista, quando couber:
  - **Decisão estrutural** (componente ou serviço novo, mudança de modelo de dados, integração assíncrona, cache, requisito de volume/latência/disponibilidade) → subagente `fluxo:arquiteto` com a funcional e o que se sabe do código. As decisões dele viram ADRs (modelo `../../templates/adr.md`), citadas na seção 9.
  - **Superfície de segurança** (autenticação, autorização, dado pessoal, pagamento, upload, integração externa, infraestrutura exposta) → subagente `fluxo:seguranca` em modo ameaças. As mitigações entram na seção 6 e viram critérios de teste na seção 8.
- Método de raciocínio: `../../referencias/raciocinio.md` (seções 1, 2, 4 e 7).

## 3. Escrever `02-tecnica.md`
- Modelo `../../templates/02-tecnica.md`. Nomes reais (classes, rotas, tabelas) e convenções do projeto; nada de "criar um serviço X" genérico.
- **Contratos**: antes/depois e compatibilidade (consumidor atual quebra? rota antiga fica como obsoleta?).
- **Estratégia de testes**: uma linha por critério de aceite (CA-n → teste unitário, contrato/integração, validação no ambiente). Critério sem teste possível → voltar à funcional.
- **Desenho mínimo**: a solução é a menor mudança no padrão atual que atende os critérios (seção 8 do método). Componente, camada, fila, cache ou dependência novos só com o requisito que os exige citado ao lado.
- **Riscos e decisões**: alternativas reais com a escolha e o motivo. Decisão que é do usuário (custo, prazo, produto) → pergunta, não escolha.
- **Dados**: para cada tabela/coleção que muda, volume atual, migração dos dados existentes (nulos, duplicados), índices para as consultas novas e rollback. Banco do perfil (`stacks`) → convenções da skill `stack-<banco>`.
- **Resiliência**: para cada integração, timeout, retry (só com idempotência), e o que acontece se ela estiver fora.
- **Implantação e CI/CD**: ordem entre componentes, migrations com rollback, feature flag quando liberar for diferente de implantar, pipelines afetadas no provedor de `ci.provedor`, e a infraestrutura (`infra`) que muda — container, manifesto, IaC — com a skill da stack correspondente.

## 4. Aprovação
- Mostrar ao usuário: componentes afetados, contratos que mudam, decisões tomadas e as que precisam dele.
- Aprovação → "aprovada em dd/mm/aaaa" no topo e sugerir `/fluxo:plano {slug}`.
