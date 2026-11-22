---
name: atualizar-conhecimento
description: Revisão periódica do conhecimento das stacks e dos especialistas do dev-flow — roda o levantamento de versões (scripts/atualizar_conhecimento.py), lê as fontes oficiais das mudanças apontadas, propõe a curadoria dos referencias/atual.md e das skills, roda a suíte de comportamento e termina numa branch com pr.md para aprovação humana, sem merge nem push. Use quando a pipeline mensal apontar achados, quando pedirem "atualiza o conhecimento das stacks", "o que mudou nas tecnologias" ou ao revisar um atual.md vencido. Só para o repositório dev-flow.
argument-hint: "[stack ...] (vazio = todas)"
---

# Atualizar o conhecimento das stacks

Funciona em qualquer host (Claude Code e Cursor leem `.claude/skills/`; em outro agente, peça para seguir este arquivo). Tudo termina numa branch revisável: **nunca** faça merge, push, publicação de versão ou alteração na `main`.

## 1. Levantar
- Branch nova a partir da `main` atualizada: `conhecimento-AAAA-MM`.
- `python -I scripts/atualizar_conhecimento.py --relatorio .claude/local/conhecimento-AAAA-MM.md` (com `--stack X` se o argumento pedir). Código 0 = nada mudou: registre "sem achados" e pare. Código 2 = há achados. Código 1 = erro (rede, formato): mostre e pare.
- Ler o relatório. A tabela de versões já foi regravada pelo script; o resto é curadoria sua.

## 2. Curar cada achado (fonte oficial antes de escrever)
Para cada item, abrir a fonte oficial listada em `## Fontes oficiais` do `atual.md` da stack (busca web ou ferramenta de documentação do host; sem acesso à web, registrar "não confirmado" e deixar para o humano).

| Achado | O que fazer |
| --- | --- |
| Ciclo novo / novo LTS | Ler release notes e guia de migração. Em `## Mudanças a observar`, um item por mudança que afeta como se implementa, testa ou revisa naquela stack: data, a partir de que versão, fonte (link) e o efeito prático. Novidade não vira regra da skill: vira item a observar. |
| Saiu de suporte | Item em "Mudanças a observar" (risco para projetos nessa versão). Modelos e exemplos dos plugins que usam essa versão → atualizar para a versão suportada (LTS quando houver). |
| Versão sem suporte citada | Atualizar a citação, ou deixá-la neutra (`<versão do projeto>`) se for exemplo genérico. Citação histórica ("antes do Go 1.22") pode ficar. |
| Revisão vencida | Reler as fontes da stack, remover itens que já não valem, atualizar `revisado_em`. |
| Falha de fonte / estrutura | Corrigir o produto ou o arquivo; não inventar dados. |

- Mudança que altera o **método** (o jeito de implementar/testar/revisar que vale em qualquer versão) → propor a edição na skill `stack-*` ou no especialista, com a fonte. Mudança de versão/recurso → só no `atual.md`.
- Ao terminar uma stack: `revisado_em` = hoje no comentário `dev-flow:conhecimento`.
- Catálogo de MCP de documentação (`plugins/fluxo/referencias/documentacao.md`): conferir em cada fonte se URL, chave e custo continuam valendo e se surgiu MCP oficial para alguma stack; atualizar `revisado_em`. Rodar `python -m unittest tests.test_mcp_documentacao` (ou a suíte inteira).
- Nada de conteúdo específico de projeto (regra do repositório).

## 3. Conferir
- `python -I scripts/atualizar_conhecimento.py --verificar` → 0.
- `python -m unittest discover -s tests` e `claude plugin validate .` (se o CLI existir).
- Se mudou skill ou especialista: suíte de comportamento com o agente disponível — `python -I scripts/avaliar_agentes.py --comando "<cli do agente>" --juiz "<cli>"` (ou `claude plugin eval plugins/fluxo` no Claude Code). Caso que piorou → reverter aquela mudança ou ajustar até passar. Sem agente de linha de comando disponível → registrar "suíte não executada" no PR.
- Versões: subir `version` dos plugins alterados (`plugin.json` + `.claude-plugin/marketplace.json`) e rodar `python -I scripts/sincronizar_hosts.py`.

## 4. Propor
- Commit na branch (mensagem `Atualiza o conhecimento das stacks (AAAA-MM)`).
- `pr.md` em `.claude/local/` com: achados do relatório, o que foi curado por stack (com links), o que ficou "não confirmado", resultado da suíte de comportamento e o que o revisor humano deve conferir.
- Parar e avisar: o push e o PR são do humano.
