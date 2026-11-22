# Medição por modelo — 22/11/2026

Comando (um por família, em paralelo; juiz fixo no `opus`; 2 execuções por caso). As variáveis forçam a família também em subagentes: sem elas, com o plugin instalado, um especialista delegado usaria o `model` do próprio frontmatter. Esta medição rodou antes de os especialistas terem `model`, então não foi afetada; repetições futuras precisam delas.

```bash
CLAUDE_CODE_SUBAGENT_MODEL=<família> CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1 \
python -I scripts/avaliar_agentes.py --comando "claude -p --model <família> --no-session-persistence --output-format json" \
  --juiz "claude -p --model opus --no-session-persistence --output-format json" --execucoes 2
```

## Acerto (casos aprovados nas 2 execuções)
| Caso | haiku | sonnet | opus |
| --- | --- | --- | --- |
| analista/campo-renomeado | 2/2 | 2/2 | 2/2 |
| arquiteto/novidade-como-sugestao | 2/2 | 2/2 | 2/2 |
| depurador/data-a-noite | 2/2 | 2/2 | 2/2 |
| revisor/projeto-primeiro | 2/2 | 2/2 | 2/2 |
| revisor/promise-sem-await | 2/2 | 2/2 | 2/2 |
| seguranca/sql-concatenado | 2/2 | 2/2 | 2/2 |
| testador/valores-limite | **1/2** (matriz incompleta numa execução) | 2/2 | 2/2 |

## Custo (US$, estimativa do `total_cost_usd` do Claude Code)
| | haiku | sonnet | opus |
| --- | --- | --- | --- |
| Total medido (agente + juiz, 14 execuções) | 2,54 | 4,05 | 5,81 |
| Juiz (≈ 0,14 por chamada × 14, medido à parte) | ≈ 1,96 | ≈ 1,96 | ≈ 1,96 |
| **Só o agente** | **≈ 0,58** | **≈ 2,09** | **≈ 3,85** |
| Relativo ao opus | ≈ 15% | ≈ 54% | 100% |

O custo do juiz foi medido com 3 chamadas avulsas do mesmo formato (US$ 0,13 a 0,17). Boa parte do custo de cada chamada é o prompt de sistema do próprio CLI (≈ 15–21 mil tokens de cache), que pesa mais nos casos pequenos da suíte do que numa tarefa real. A partir desta demanda, a suíte separa o custo do agente e o do juiz.

## Decisão (RN-1 e julgamento sobre a cobertura)
A suíte tem 1 ou 2 casos por especialista: passar neles é condição necessária, não suficiente. Desce-se até o modelo em que o especialista passou em todas as execuções, exceto onde o erro custa caro de pegar depois (aí fica um nível acima, ou no modelo da sessão):

| Especialista | Modelo | Motivo |
| --- | --- | --- |
| `analista` | `haiku` | Leitura e levantamento (muitos tokens), passou 2/2 no haiku; a técnica e o arquiteto revisam o que ele traz. |
| `revisor` | `sonnet` | Passou 2/2 no haiku, mas é a porta de qualidade do commit: margem de um nível. |
| `depurador` | `sonnet` | Passou 2/2 no haiku; a causa raiz é conferida pelo teste de regressão, mas hipóteses ruins custam tempo. |
| `testador` | `sonnet` | Falhou 1/2 no haiku (matriz incompleta); 2/2 no sonnet. |
| `arquiteto` | `inherit` | Decisão estrutural cara de desfazer; 1 caso não basta para descer. |
| `seguranca` | `inherit` | Achado perdido custa caro; 1 caso não basta para descer. |
| `validador` | `inherit` | Sem caso de comportamento (depende de ambiente). |
| `designer`, `analista-de-logs` | `inherit` | Sem caso de comportamento. |

Rever quando a suíte ganhar casos (cada caso novo por especialista é chance de descer mais um nível com segurança).

## Conferência depois da revisão (22/11/2026)
Verificadores regex do `analista` e do `depurador` ficaram mais rígidos (exigem o contexto, não a palavra solta). Rodados de novo no modelo escolhido, com a família forçada também nos subagentes (`CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`), 2 execuções:

| Caso | Modelo | Resultado | Custo do agente (2 execuções) |
| --- | --- | --- | --- |
| analista/campo-renomeado | haiku | 2/2 | US$ 0,02 |
| depurador/data-a-noite | sonnet | 2/2 | US$ 0,37 |

Com o custo do agente separado do juiz, o `analista` no haiku saiu bem abaixo da estimativa acima (≈ US$ 0,01 por execução).
