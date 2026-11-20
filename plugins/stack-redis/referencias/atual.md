# Conhecimento atual: Redis
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=redis -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://github.com/redis/redis/releases
- https://redis.io/docs/latest/
- https://endoflife.date/redis (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| redis | 8.10 | suportado | 2026-07-29 | sim | — | 8.10.3 |
| redis | 8.8 | suporte ativo encerrado | 2026-05-25 | 2026-07-29 | — | 8.8.4 |
| redis | 8.6 | suporte ativo encerrado | 2026-02-11 | 2026-05-25 | — | 8.6.8 |
| redis | 8.4 | suporte ativo encerrado | 2025-11-18 | 2026-02-11 | — | 8.4.8 |
| redis | 8.2 | suporte ativo encerrado | 2025-08-04 | 2025-11-18 | 2030-09-01 | 8.2.11 |
| redis | 8.0 | suporte ativo encerrado | 2025-05-02 | 2025-08-04 | 2026-12-01 | 8.0.6 |
| redis | 7.4 | suporte ativo encerrado | 2024-07-29 | 2025-05-02 | 2029-12-01 | 7.4.12 |
| redis | 7.2 | suporte ativo encerrado | 2023-08-15 | 2024-07-29 | 2029-12-01 | 7.2.17 |
| redis | 6.2 | suporte ativo encerrado | 2021-02-22 | 2022-04-27 | 2027-04-01 | 6.2.24 |
| redis | 7.0 | sem suporte | 2022-04-27 | 2023-08-15 | 2024-07-29 | 7.0.15 |
| redis | 6.0 | sem suporte | 2020-04-30 | 2021-02-22 | 2022-05-31 | 6.0.20 |
<!-- versoes:fim -->

## O que acompanhar
- Fim de suporte da versão do servidor e do serviço gerenciado (ou alternativa compatível adotada).
- Licença e compatibilidade de clientes ao trocar de versão principal.

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
