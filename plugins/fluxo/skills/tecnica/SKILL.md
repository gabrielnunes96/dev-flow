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

## 3. Escrever `02-tecnica.md`
- Modelo `../../templates/02-tecnica.md`. Nomes reais (classes, rotas, tabelas) e convenções do projeto; nada de "criar um serviço X" genérico.
- **Contratos**: antes/depois e compatibilidade (consumidor atual quebra? rota antiga fica como obsoleta?).
- **Estratégia de testes**: uma linha por critério de aceite (CA-n → teste unitário, contrato/integração, validação no ambiente). Critério sem teste possível → voltar à funcional.
- **Riscos e decisões**: alternativas reais com a escolha e o motivo. Decisão que é do usuário (custo, prazo, produto) → pergunta, não escolha.
- **Implantação e CI/CD**: ordem entre componentes, migrations com rollback, pipelines afetadas.

## 4. Portão
- Mostrar ao usuário: componentes afetados, contratos que mudam, decisões tomadas e as que precisam dele.
- Aprovação → "aprovada em dd/mm/aaaa" no topo e sugerir `/fluxo:plano {slug}`.
