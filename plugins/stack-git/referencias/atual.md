# Conhecimento atual: Git
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=git -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://github.com/git/git/tree/master/Documentation/RelNotes (notas de cada versão)
- https://git-scm.com/docs/BreakingChanges (mudanças de padrão previstas para o Git 3.0)
- https://git-scm.com/docs (manual da versão)
- https://endoflife.date/git (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| git | 2.56 | suportado | 2026-09-28 | sim | — | 2.56.1 |
| git | 2.55 | suporte ativo encerrado | 2026-06-29 | 2026-09-28 | — | 2.55.1 |
| git | 2.54 | suporte ativo encerrado | 2026-04-20 | 2026-06-29 | — | 2.54.1 |
| git | 2.53 | suporte ativo encerrado | 2026-02-02 | 2026-04-20 | — | 2.53.1 |
| git | 2.52 | suporte ativo encerrado | 2025-11-17 | 2026-02-02 | — | 2.52.1 |
| git | 2.51 | suporte ativo encerrado | 2025-08-18 | 2025-11-17 | — | 2.51.3 |
| git | 2.50 | suporte ativo encerrado | 2025-06-16 | 2025-08-18 | — | 2.50.2 |
| git | 2.49 | suporte ativo encerrado | 2025-03-14 | 2025-06-16 | — | 2.49.1 |
| git | 2.48 | suporte ativo encerrado | 2025-01-10 | 2025-03-14 | — | 2.48.2 |
| git | 2.47 | sem suporte | 2024-10-07 | 2025-01-10 | 2025-10-15 | 2.47.3 |
| git | 2.46 | sem suporte | 2024-07-29 | 2024-10-07 | 2025-07-08 | 2.46.4 |
<!-- versoes:fim -->

## O que acompanhar
- Versão do Git dos runners de CI e das imagens (recurso novo de `git` em script de CI só se o runner tiver).
- Mudanças de padrão anunciadas para o Git 3.0 (nome da branch inicial, formato de objetos): seguir a configuração explícita do projeto.

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
