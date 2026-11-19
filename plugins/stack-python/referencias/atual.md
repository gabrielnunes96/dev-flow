# Conhecimento atual: Python
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=python,django -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://devguide.python.org/versions/
- https://docs.python.org/3/whatsnew/
- https://www.djangoproject.com/download/#supported-versions
- https://endoflife.date/python (suporte e fim de vida; fonte da tabela abaixo)
- https://endoflife.date/django (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| python | 3.15 | suportado | 2026-10-09 | 2028-10-09 | 2031-10-31 | 3.15.2 |
| python | 3.14 | suportado | 2025-10-07 | 2027-10-01 | 2030-10-31 | 3.14.10 |
| python | 3.13 | suporte ativo encerrado | 2024-10-07 | 2026-10-01 | 2029-10-31 | 3.13.18 |
| python | 3.12 | suporte ativo encerrado | 2023-10-02 | 2025-04-02 | 2028-10-31 | 3.12.16 |
| python | 3.11 | suporte ativo encerrado | 2022-10-24 | 2024-04-01 | 2027-10-31 | 3.11.18 |
| python | 3.10 | sem suporte | 2021-10-04 | 2023-04-05 | 2026-10-01 | 3.10.22 |
| python | 3.9 | sem suporte | 2020-10-05 | 2022-05-17 | 2025-10-31 | 3.9.25 |
| django | 6.1 | suportado | 2026-08-05 | 2027-04-30 | 2027-12-31 | 6.1.3 |
| django | 6.0 | suporte ativo encerrado | 2025-12-03 | 2026-08-04 | 2027-04-30 | 6.0.10 |
| django | 5.2 | LTS | 2025-04-02 | 2025-12-03 | 2028-04-30 | 5.2.19 |
| django | 5.1 | sem suporte | 2024-08-07 | 2025-04-02 | 2025-12-03 | 5.1.15 |
| django | 5.0 | sem suporte | 2023-12-04 | 2024-08-07 | 2025-04-02 | 5.0.14 |
<!-- versoes:fim -->

## O que acompanhar
- Versão nova anual e fim de suporte; `requires-python`, imagem base e CI.
- Mudanças de frameworks (Django LTS, FastAPI/Pydantic, SQLAlchemy) e de ferramentas (uv, ruff).

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
