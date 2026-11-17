---
name: python
description: Convenções e armadilhas de Python para implementar, testar e revisar tarefas do fluxo — FastAPI, Django e Flask, tipagem com mypy/pyright, pytest com fixtures e parametrize, ruff, ambientes virtuais (uv, poetry, pip), async, pydantic, SQLAlchemy/Alembic e pacotes vulneráveis. Use ao implementar ou revisar código Python num projeto com stack python.
---

# Python no fluxo

As convenções do **projeto** (CLAUDE.md, `pyproject.toml`, configuração do ruff/mypy) vencem estas quando conflitarem.

## Implementar
- Descubra o gerenciador antes de instalar algo: `uv.lock` → `uv`; `poetry.lock` → `poetry`; `Pipfile.lock` → `pipenv`; senão `pip` com `requirements*.txt`. Rode tudo **dentro do ambiente do projeto** (`uv run`, `poetry run`, `.venv`), nunca no Python global.
- Siga a operação existente mais parecida de ponta a ponta (rota → schema/serializer → serviço → repositório/ORM → teste). FastAPI: dependências por `Depends`, schemas pydantic separados de entrada e saída; Django: lógica fora da view (serviço/manager), migrations geradas por `makemigrations` e revisadas; Flask: blueprints e factory.
- Tipagem em todo código novo (parâmetros e retorno). `Optional[X]`/`X | None` só quando `None` é um valor legítimo, e então trate.
- Pydantic v2: `model_validate`/`model_dump`, não os nomes da v1. Validação de entrada na fronteira, com mensagem que nomeia o campo.
- Dinheiro em `Decimal` (nunca `float`), datas com fuso (`datetime.now(tz=UTC)`; nada de `utcnow()` ingênuo).
- Armadilhas: argumento padrão mutável (`def f(x=[])`), `except Exception: pass`, `except:` sem tipo, comparação com `is` para valores, import circular, `async def` que chama código bloqueante (I/O síncrono, `time.sleep`, `requests`) dentro do event loop — use a lib async (`httpx.AsyncClient`, driver async) ou `run_in_executor`.
- SQLAlchemy: sessão por requisição/unidade de trabalho, `select()` 2.0, carregamento explícito (`selectinload`) para evitar N+1. Alembic: migração revisada à mão, com `downgrade` funcional.
- Segredos de variáveis de ambiente/cofre (pydantic-settings), nunca no código; `.env` fora do git.
- Logs com `logging` (não `print`), sem dado sensível; mensagens com contexto (`extra=`).

## Testar
- `comandos.teste` do perfil (tipicamente `pytest -q`), `comandos.lint` (`ruff check` + `ruff format --check`) e, se o projeto usa, `mypy`/`pyright`. Todos verdes.
- pytest: fixtures para montar estado, `@pytest.mark.parametrize` para a matriz de casos, `tmp_path` para arquivos, `monkeypatch` para ambiente. Tempo injetado (ou `freezegun`/`time-machine` se o projeto já usa).
- API: `TestClient` (FastAPI/Starlette) ou cliente de teste do Django contra a app em memória, conferindo status, corpo e nomes de campos do JSON.
- Banco: o padrão do projeto (SQLite em memória só se o projeto já aceita; diferenças de dialeto escondem bug — prefira o mesmo banco via container quando houver).
- HTTP externo: `respx`/`responses`/`pytest-httpx` conferindo método, URL e corpo enviados.
- Vulnerabilidades: `comandos.vulnerabilidades` (ex.: `pip-audit`, `uv pip audit`) ao mexer em dependências; versão fixada no lock.

## Checklist de revisão
1. Tipos em funções novas; nenhum `Any`/`# type: ignore` novo sem motivo comentado.
2. Nenhum argumento padrão mutável; nenhum `except` genérico que engole erro.
3. Async sem chamada bloqueante; `await` em toda corrotina.
4. `Decimal` para dinheiro; `datetime` com fuso.
5. Consultas sem N+1; sessão/transação fechadas; migração com `downgrade`.
6. Entrada validada na fronteira (pydantic/serializer/form); erro 4xx nomeia o campo.
7. Sem segredo no código, sem `print` de depuração, sem dado sensível em log.
8. Dependência nova declarada no `pyproject.toml`/lock do gerenciador do projeto.
