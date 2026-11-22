# Modelo por especialista e MCP de documentação — Especificação funcional

> Demanda: `modelo-e-documentacao` · Versão 1 · 22/11/2026 · Situação: **aprovada em 22/11/2026** (por delegação do usuário nesta sessão)

## 1. Objetivo
Gastar menos com os especialistas que não precisam do modelo mais forte, sem perder acerto (com medição), e dar aos agentes a documentação da versão em uso por MCP em vez de memória.

## 2. Contexto
- Os especialistas não fixam modelo: herdam o da sessão. Um `analista` que só lê e busca custa o mesmo que um `arquiteto`.
- A suíte de comportamento (`scripts/avaliar_agentes.py`) mede acerto, mas não custo.
- O passo 3 do procedimento *projeto primeiro* já prefere "ferramenta de documentação do host", mas nada diz qual usar nem como ligar.
- Fatos dos hosts (consultados em 22/11/2026): Claude Code aceita `model` no frontmatter do subagente (`haiku`/`sonnet`/`opus`/`inherit` ou ID; apelido = versão mais nova da família) e permite sobrescrever tudo com `CLAUDE_CODE_SUBAGENT_MODEL` + `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`; o Cursor aceita `inherit` ou ID específico e não lê subagente de plugin; Agent Skills não tem campo de modelo. MCP remoto de projeto: `.mcp.json` (Claude Code, `type: "http"`) e `.cursor/mcp.json` (Cursor, só `url`).

## 3. Atores
Sessão e especialistas do fluxo; mantenedor do dev-flow; time que configura o projeto (`iniciar`).

## 4. Escopo
**Dentro**: custo por caso na suíte; casos para `analista` e `depurador`; medição por modelo; `model` no frontmatter dos especialistas conforme a medição; catálogo datado de MCPs de documentação por stack; script que gera a configuração por host; `iniciar`, `conhecimento.md`, `hosts.md`, README e manual.
**Fora**: MCP próprio do dev-flow, RAG, fine-tuning, ligar MCP automaticamente ao instalar plugin.

## 5. Regras de negócio
- RN-1: especialista só desce para um modelo em que, na medição, passou em todos os casos dele em todas as execuções; sem caso de comportamento, fica `inherit`.
- RN-2: modelo é escrito por família (apelido), nunca por versão; nome de versão é conhecimento volátil.
- RN-3: MCP de documentação é opcional e ligado pelo humano (a sessão mostra a configuração; não grava sozinha), como as permissões no `iniciar`.
- RN-4: catálogo de MCPs (URL, custo, chave) é conhecimento volátil: arquivo datado, com fonte, revisto pela revisão periódica.
- RN-5: nada muda para hosts sem suporte a modelo por subagente; o time pode sobrescrever tudo sem editar o plugin.

## 6. Requisitos funcionais
- RF-1: `avaliar_agentes.py` lê a saída JSON do agente quando houver (`result`, `total_cost_usd`) e soma custo por caso e total; texto puro continua funcionando.
- RF-2: casos de comportamento para `analista` e `depurador`.
- RF-3: tabela de medição (acerto e custo por especialista e modelo) registrada na demanda.
- RF-4: `model` no frontmatter dos especialistas conforme RF-3/RN-1; `hosts.md` explica o comportamento por host e como sobrescrever.
- RF-5: `fluxo/referencias/documentacao.md`: MCPs de documentação por stack (nome, URL, chave/custo, observação de versão), com data e fontes.
- RF-6: `fluxo/scripts/mcp_documentacao.py --host claude|cursor [--perfil]` gera o JSON a mesclar, a partir das stacks do perfil.
- RF-7: `iniciar` oferece o MCP de documentação; `conhecimento.md` passo 3 aponta o catálogo e diz como pedir a versão.

## 7. Requisitos não funcionais
Scripts só com a biblioteca padrão; testes em `tests/`; pt-BR.

## 8. Critérios de aceite
- CA-1: com um agente falso que devolve JSON com `result` e `total_cost_usd`, a suíte avalia o `result` e soma o custo; com texto puro, custo "—".
- CA-2: `analista` e `depurador` têm caso válido (estrutura testada como os demais).
- CA-3: `medicao.md` traz a tabela por modelo com data e comando.
- CA-4: todo especialista do `fluxo` tem `model` com valor em {`haiku`, `sonnet`, `opus`, `inherit`} e o teste confere.
- CA-5: `documentacao.md` tem data de revisão e fonte por MCP; toda stack do perfil tem ao menos uma fonte (MCP ou "busca web").
- CA-6: o script gera JSON válido para `claude` (`type: "http"`) e `cursor` (só `url`), sem duplicar servidor, só para as stacks do perfil; perfil ausente → erro com código 1.
- CA-7: README, manual, `hosts.md` e `iniciar` atualizados; versões publicadas.

## 9. Impacto em consumidores
Especialistas com `model` fixo passam a usar outra família no Claude Code; quem quiser manter tudo no modelo da sessão usa as variáveis documentadas. Nada muda nos outros hosts.

## 10. Dúvidas em aberto
Nenhuma.
