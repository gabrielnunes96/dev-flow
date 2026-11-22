# Modelo por especialista e MCP de documentação — Especificação técnica

> Demanda: `modelo-e-documentacao` · 22/11/2026 · Situação: **aprovada em 22/11/2026** (por delegação do usuário nesta sessão)

## 1. Visão da solução
1. Medir antes de mudar: a suíte ganha custo e casos novos; roda-se cada caso com `claude -p --model <família>` (juiz fixo no `opus`) e registra-se a tabela.
2. Aplicar a medição no frontmatter (`model:`), por família.
3. Catálogo de MCP de documentação + gerador de configuração por host, oferecido pelo `iniciar`.

## 2. Componentes afetados
| Componente | Mudança |
| --- | --- |
| `scripts/avaliar_agentes.py` | `extrair(saida)`: JSON com `result` → (texto, custo); soma por caso/total; coluna de custo na saída e no `--json`. |
| `plugins/fluxo/evals/{analista,depurador}/` | um caso cada (regex + llm). |
| `plugins/fluxo/agents/*.md`, `design/agents/designer.md`, `logs/agents/analista-de-logs.md` | `model:` conforme medição (sem caso → `inherit`). |
| `plugins/fluxo/referencias/documentacao.md` | catálogo datado (meta `dev-flow:conhecimento`). |
| `plugins/fluxo/scripts/mcp_documentacao.py` | gerador por host. |
| `plugins/fluxo/referencias/{conhecimento,hosts}.md`, `skills/iniciar/SKILL.md` | passo 3, comportamento por host, oferta no iniciar. |
| `.claude/skills/atualizar-conhecimento/SKILL.md` | revisar também o catálogo. |
| README, manual, versões | — |

## 3. Contratos
- Saída do agente: se `json.loads(stdout)` é objeto com `result` (str) → resposta = `result`, custo = `total_cost_usd` (número) se houver.
- `documentacao.md`: tabela `| MCP | URL | Chave | Custo | Stacks | Versão |`, linhas de dados com URL `https://`; stacks separadas por vírgula; `*` = todas.
- `mcp_documentacao.py`: saída `{"mcpServers": {...}}`; Claude: `{"type": "http", "url": ...}`; Cursor: `{"url": ...}`. Códigos: 0 ok, 1 erro (perfil ausente/ inválido, catálogo mal formado).

## 4. Dados
Nenhum.

## 5. Integrações externas
Anthropic (medição, custo de quem roda); MCPs remotos de documentação (opcionais, ligados pelo humano).

## 6. Segurança
MCP remoto recebe as perguntas do agente (nome de biblioteca, trecho de dúvida): o catálogo avisa; nada de segredo na consulta. Chave de API, quando houver, por variável de ambiente (`${env:...}` no Cursor), nunca no arquivo versionado. Configuração gravada pelo humano.

## 7. Observabilidade
Custo por caso na suíte.

## 8. Estratégia de testes
| CA | Teste |
| --- | --- |
| CA-1 | `tests/test_avaliar_agentes.py` com agente falso em JSON e em texto. |
| CA-2 | estrutura dos casos (teste existente cobre os novos). |
| CA-3 | existência e cabeçalho de `medicao.md`. |
| CA-4 | `tests/test_marketplace.py`: `model` válido em todo especialista. |
| CA-5, CA-6 | `tests/test_mcp_documentacao.py`. |
| CA-7 | testes de texto + `claude plugin validate`. |

## 9. Riscos e decisões
- Medição com 1 execução tem ruído → 2 execuções por modelo nos candidatos a descer; desce só se passar em todas (RN-1).
- `haiku` em especialista que edita (`testador`) pode errar em código → só com medição.
- Apelido resolve para versão antiga em Bedrock/Vertex: documentado em `hosts.md`.

## 10. Implantação e rollback
`fluxo` 0.5.0 (muda comportamento de custo), `design`/`logs` se mudarem; rollback = reverter o merge ou `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`.

## 11. CI/CD
Sem mudança.
