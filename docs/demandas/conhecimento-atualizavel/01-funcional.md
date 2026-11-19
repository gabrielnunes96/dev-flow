# Conhecimento atualizável dos agentes — Especificação funcional

> Demanda: `conhecimento-atualizavel` · Versão 1 · 19/11/2026 · Situação: **aprovada em 19/11/2026** (por delegação do usuário nesta sessão: "você está livre para fazer o que quiser")

## 1. Objetivo
Evitar que as skills e os especialistas do dev-flow fiquem defasados conforme linguagens, frameworks, bancos, ferramentas e modelos de IA evoluem, sem que o mantenedor precise lembrar de revisá-los — e sem que um agente aplique novidade num projeto que segue outro padrão.

## 2. Contexto
- Hoje o conhecimento de cada stack está escrito à mão nas skills `stack-*` e nos agentes (`fluxo/agents/*.md`, `design/agents/designer.md`). Ele só muda quando alguém lembra de editar.
- As skills já dizem que "as convenções do projeto vencem", mas não há um procedimento único para o agente descobrir a versão em uso nem para consultar a documentação daquela versão.
- Os agentes não fixam `model:` (herdam o da sessão) e as skills citam poucas versões — bom ponto de partida.
- A skill `aprender` grava aprendizados no projeto, mas não leva os que valem para toda uma stack de volta ao dev-flow de forma organizada.
- Não existe teste de comportamento dos agentes: uma edição de skill pode piorar um revisor sem que ninguém perceba.

## 3. Atores
| Ator | Papel |
| --- | --- |
| Mantenedor do dev-flow | Aprova (ou não) as atualizações propostas; faz merge e publica versão |
| Agente/skill em uso num projeto | Aplica o conhecimento respeitando o projeto |
| Revisão periódica (robô) | Levanta o que mudou nas fontes e propõe atualização |
| Time consumidor | Recebe as atualizações pelo marketplace |

## 4. Escopo
**Dentro:**
- Separar, por stack, o **método** (estável, nas skills) do **conhecimento volátil** (versões suportadas, LTS, fim de suporte, mudanças a observar, fontes oficiais), com data de revisão.
- Um procedimento único "projeto primeiro" que todo especialista e skill de stack segue antes de propor ou escrever código.
- Uma escolha no perfil do projeto sobre o que fazer com novidades (só sugerir, ou aplicar em projeto novo).
- Levantamento automático e reproduzível do estado das versões (suporte/LTS/fim de vida) a partir de fonte pública, com relatório do que mudou e do que nas skills ficou defasado.
- Revisão periódica agendada que produz o relatório e uma proposta de atualização para aprovação humana.
- Casos de teste de comportamento para os especialistas, executáveis antes de aceitar uma atualização.
- Caminho da skill `aprender` para propor ao dev-flow os aprendizados que valem para uma stack inteira.
- Documentação (README, manual, CLAUDE.md).

**Fora (explícito):**
- Merge ou publicação automática de atualização (sempre passa por aprovação humana).
- Atualizar automaticamente o código dos projetos consumidores para versões novas.
- Fixar modelo de IA por agente ou escolher modelo automaticamente.
- Instalar ou configurar MCP de documentação na máquina do usuário (é configuração do host; o fluxo só usa se existir).
- Reescrever o processo (demanda → técnica → plano → task → PR).

## 5. Regras de negócio
| ID | Regra | Origem |
| --- | --- | --- |
| RN-1 | O padrão do projeto vence o conhecimento do agente: antes de escrever código, o agente identifica convenções e a versão em uso no projeto. | Usuário |
| RN-2 | Novidade que o projeto não usa é **sugestão** (no fechamento ou em ADR), não mudança — salvo se o perfil disser que o projeto aceita aplicar novidades ou se a demanda pedir. | Usuário |
| RN-3 | Só versão estável/suportada é recomendada; versão sem suporte (fim de vida) é sinalizada como risco; preferir LTS quando a tecnologia tiver LTS. | Usuário ("espera sair a LTS") |
| RN-4 | Nenhuma atualização do conhecimento entra sem aprovação humana. | Proposta aceita |
| RN-5 | Conhecimento volátil não fica no texto do método: fica num arquivo por stack com data de revisão e fontes. | Proposta aceita |
| RN-6 | Uma atualização de skill/agente só é aceita se os testes de comportamento não piorarem. | Proposta aceita |
| RN-7 | Nada específico de projeto dentro de skill (regra do repositório). | CLAUDE.md |
| RN-8 | Tudo funciona em qualquer host (Claude Code, Cursor, outros agentes com Agent Skills e CLIs como `codex`): nada da solução depende de um recurso exclusivo de um host; recurso de host é atalho opcional. | Usuário (19/11/2026) |

## 6. Requisitos funcionais
| ID | Requisito | Regras |
| --- | --- | --- |
| RF-1 | Cada plugin de stack deve ter um arquivo de conhecimento atual com: data de revisão, produtos rastreados, fontes oficiais, tabela de versões (gerada) e mudanças a observar. | RN-3, RN-5 |
| RF-2 | Deve existir um procedimento "projeto primeiro" (convenções → versão em uso → documentação daquela versão → novidade como sugestão), citado por todos os especialistas e skills de stack. | RN-1, RN-2 |
| RF-3 | O perfil do projeto deve aceitar a política de novidades (`sugerir` ou `aplicar`), com `sugerir` como padrão. | RN-2, RN-7 |
| RF-4 | Um script deve regenerar a tabela de versões de cada stack a partir de fonte pública e listar o que mudou: ciclo novo, ciclo que perdeu suporte, LTS novo, versão citada em skill que já está sem suporte, arquivo com revisão vencida. | RN-3 |
| RF-5 | O mesmo script deve ter um modo de verificação offline (sem rede) para os testes: estrutura dos arquivos e revisão vencida. | RN-5 |
| RF-6 | Deve existir uma rotina periódica (pipeline agendada) que roda o levantamento e publica o relatório; e uma skill de manutenção que transforma o relatório numa proposta de atualização revisável (branch + PR), sem merge. | RN-4 |
| RF-7 | Deve existir uma suíte de testes de comportamento dos especialistas (casos com entrada e o que a saída deve conter), executável antes de aceitar a atualização, com qualquer agente de linha de comando (não só Claude). | RN-6, RN-8 |
| RF-8 | A skill `aprender` deve encaminhar aprendizado que vale para uma stack inteira como proposta ao arquivo de conhecimento da stack. | RN-4, RN-5 |

## 7. Requisitos não funcionais
- Scripts só com biblioteca padrão do Python; rodam com `python -I`.
- O levantamento online tolera falha de rede por produto (relata e segue) e não grava nada parcial.
- Testes do repositório continuam offline e rápidos.
- Funciona em Claude Code, Cursor e Agent Skills (texto host-agnóstico; exportação leva os novos arquivos).

## 8. Critérios de aceite
- **CA-1** (RF-1) — Dado o repositório, quando os testes rodam, então todo plugin `stack-*` tem `referencias/atual.md` com data de revisão, ao menos uma fonte oficial e o bloco de versões; e a skill da stack cita esse arquivo.
- **CA-2** (RF-2) — Dado qualquer especialista do `fluxo` ou o `designer`, ou qualquer skill de stack, quando o texto é lido, então ele cita o procedimento "projeto primeiro" (`referencias/conhecimento.md`).
- **CA-3** (RF-3) — Dado um perfil com `conhecimento.novidades = "aplicar"`, quando `perfil.py validar` roda, então passa; com valor fora de `sugerir|aplicar`, falha com mensagem; sem o campo, passa (padrão `sugerir`).
- **CA-4** (RF-4) — Dado uma resposta da fonte com um ciclo novo, um ciclo que perdeu suporte desde a última revisão e um LTS novo, quando o levantamento roda, então o relatório lista os três e o bloco de versões é regenerado.
- **CA-5** (RF-4) — Dado uma skill que cita uma versão cujo ciclo está sem suporte, quando o levantamento roda, então o relatório aponta arquivo e linha.
- **CA-6** (RF-4, RNF) — Dado falha de rede em um produto, quando o levantamento roda, então os demais são atualizados, o produto com falha aparece no relatório e o arquivo daquela stack não é alterado.
- **CA-7** (RF-5) — Dado um arquivo de conhecimento com revisão mais velha que o limite, quando a verificação offline roda, então sai com código diferente de zero e diz qual.
- **CA-8** (RF-6) — Dado o repositório, então existe pipeline agendada que roda o levantamento e publica o relatório, e uma skill de manutenção que proíbe merge/push automático e termina em branch + descrição de PR.
- **CA-9** (RF-7) — Dado a suíte de comportamento, quando os testes do repositório rodam, então todo caso tem especialista existente, entrada e verificações; e há instrução de como executá-la contra o modelo.
- **CA-11** (RF-7, RN-8) — Dado um comando de agente qualquer configurado (ex.: um `echo`/script falso nos testes), quando o executor da suíte roda, então ele envia o prompt de cada caso ao comando, aplica as verificações à saída e devolve código 0 se todos passam e 1 se algum falha.
- **CA-12** (RN-8) — Dado os textos novos (procedimento, skill de manutenção, documentação), quando lidos, então não exigem recurso de um host específico; quando citam um (MCP, subagente, rotina agendada), oferecem alternativa genérica.
- **CA-10** (RF-8) — Dado a skill `aprender`, quando lida, então a linha "vale para qualquer projeto da stack" aponta para `referencias/atual.md` (ou a skill) do plugin da stack via proposta ao dev-flow.

## 9. Impacto em consumidores
- Times que usam o marketplace recebem novos arquivos e um campo opcional no perfil; nada quebra (campo novo é opcional).
- Projetos com skills exportadas precisam exportar de novo para receber `referencias/`.

## 10. Dúvidas em aberto
| # | Dúvida | Para quem | Resposta |
| --- | --- | --- | --- |
| D-1 | Frequência da revisão periódica | Usuário | Não bloqueante: mensal (1º dia útil), ajustável no YAML |
| D-2 | Testes de comportamento rodam no CI a cada PR? | Usuário | Não bloqueante: não (custam chamada de modelo); rodam na revisão periódica e sob demanda |
