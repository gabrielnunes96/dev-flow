# Conceitos: qual peça resolve qual problema

O aprendizado central do PBI 1001: cada peça do Claude Code resolve um problema diferente. Misturá-las é o que deixa a automação frágil — regra de processo no CLAUDE.md custa contexto em toda mensagem, proibição escrita só em texto é esquecida, procedimento mecânico deixado ao modelo varia a cada execução.

| Peça | O que é | Use para | Não use para | No fluxo |
| --- | --- | --- | --- | --- |
| **CLAUDE.md / rules** | Contexto carregado **sempre** | Fatos do projeto: arquitetura, convenções, armadilhas | Processo passo a passo (vira skill); proibições (viram hook) | `CLAUDE.md` do projeto, `.claude/rules/` |
| **Skill** | Procedimento carregado **sob demanda** quando a descrição bate com o pedido; leva modelos e scripts | "Como fazer X": especificar, planejar, o ciclo da tarefa | Fatos do projeto (ficam no perfil/CLAUDE.md) | `fluxo:*`, `stack-*`, `azure-*` |
| **Script** | Código determinístico chamado pela skill | Tudo que não precisa de raciocínio: token, subir app, lote HTTP, fila de tarefas | Decisões | `scripts/*.py` |
| **Agente** | Contexto isolado, ferramentas restritas, devolve um resumo | Trabalho barulhento ou que deve ser independente: revisão, validação, análise de impacto, tarefas em paralelo | Coisas que precisam da conversa toda | `analista`, `revisor`, `validador` |
| **Hook** | Executado pelo harness, não pelo modelo — **garantia** | O que nunca pode acontecer; contexto automático no início da sessão | Orientação que admite exceção | `guard.py`, `contexto.py` |
| **MCP** | Conexão com sistema externo | Ler/escrever em Boards, banco, APIs internas | Processo (não é lugar de "como trabalhar") | MCP do Azure DevOps |
| **Plugin / marketplace** | Pacote versionado de skills, agentes, hooks e MCP | Reaproveitar tudo isso entre projetos e com o time | — | este repositório |
| **Perfil** (`projeto.json`) | Contrato entre o processo genérico e o projeto | Comandos, rastreador, validação, proteções | Texto livre (vai no CLAUDE.md) | `.claude/projeto.json` |

## Por que plugin e não um MCP próprio

MCP dá ao modelo **acesso** a sistemas. O fluxo de desenvolvimento é **conhecimento procedural** (como especificar, quebrar, implementar, validar) — isso é skill. Um MCP próprio só se justifica quando faltar acesso a algo (ex.: um MCP "ambientes da empresa" que entregue tokens de homologação e dados de teste ao time inteiro, no lugar do `token_login.py` de cada máquina).

## Decisões de desenho

1. **Processo genérico, projeto no perfil.** A `proxima-task` original tinha "PBI 1001", "porta 5009" e "V6/Extended" no texto; a `fluxo:task` lê tudo do perfil. Um projeto novo não exige mexer no plugin.
2. **Especificações e fila como arquivo.** `tarefas.json` é a fonte da verdade; o Boards é um espelho opcional. A fila sobrevive a compactação, troca de sessão e falta de conexão.
3. **Portões humanos explícitos.** Funcional, técnica e plano só avançam com aprovação registrada no topo do documento. Entre portões, o fluxo segue sem pedir confirmação. Push, merge e deploy em produção são do usuário.
4. **Definição de pronto verificável.** Critério de aceite → teste → validação no ambiente → commit → registro. O revisor confere critério a critério.
5. **Proteção por hook, dirigida pelo perfil.** Diretório excluído, código gerado, segredo, push: o guard bloqueia de verdade, e cada projeto declara os seus.
6. **Determinístico onde dá.** `plano.py` (fila, dependências, ciclos), `http_lote.py` (lote com status esperado e tabela do card), `servico.py` (subir/derrubar com healthcheck), `token_login.py` (login com certificado fixado). Testados em `tests/`.
7. **Aprender é uma etapa.** `/fluxo:aprender` classifica cada correção no lugar certo (perfil, CLAUDE.md, dados do ambiente, skill de stack, plugin) — por exemplo, "o sandbox aceita qualquer ID" foi parar nos dados do ambiente, não como impedimento na daily.

## Onde o tempo é ganho

- Retomar sem recapitular: o hook de contexto diz a demanda ativa e a próxima tarefa ao abrir a sessão.
- Scripts no lugar de improviso em tudo que é mecânico.
- Tarefas sem dependência entre si em paralelo (`plano.py prontas` + agentes em worktree).
- Menos prompts de permissão: `/fluxo:iniciar` propõe a allowlist dos comandos do perfil.
- CLAUDE.md enxuto: processo mora em skill e só carrega quando usado.
- Mesmos comandos no local e no CI (o pipeline usa `comandos` do perfil).
