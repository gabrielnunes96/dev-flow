---
name: depurador-data-a-noite
description: Depurador acha a causa raiz de um teste que só falha à noite na máquina do desenvolvedor
tags: [depurador, comportamento]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Agent]
---

Aja como o especialista `depurador` do plugin fluxo (no Claude Code, o subagente `fluxo:depurador`; em outro host, siga `agents/depurador.md`). Não há repositório nem como executar: investigue só com o material abaixo, de um projeto Python 3.13 com pytest.

Sintoma relatado: "o teste `test_boleto_que_vence_hoje_nao_esta_vencido` falha na máquina dos desenvolvedores (São Paulo) só depois das 21h; de manhã e à tarde passa. No CI passa sempre."

`cobranca/boletos.py`
```python
from dataclasses import dataclass
from datetime import date, datetime, timezone

@dataclass
class Boleto:
    vencimento: date

def esta_vencido(boleto: Boleto) -> bool:
    return boleto.vencimento < datetime.now(timezone.utc).date()
```

`tests/test_boletos.py`
```python
from datetime import date
from cobranca.boletos import Boleto, esta_vencido

def test_boleto_que_vence_hoje_nao_esta_vencido():
    assert not esta_vencido(Boleto(vencimento=date.today()))
```

Saída de uma execução às 22h10:
```
FAILED tests/test_boletos.py::test_boleto_que_vence_hoje_nao_esta_vencido - assert not True
```

Devolva a investigação no formato do especialista.
