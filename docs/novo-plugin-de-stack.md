# Como criar um plugin de stack

Uma stack nova (ex.: `rust`, `angular` separado de `front`, `elasticsearch`) é um plugin pequeno com uma skill. O núcleo `fluxo` a encontra pelo nome em `stacks` do perfil.

```
plugins/stack-<nome>/
  .claude-plugin/plugin.json      name: stack-<nome>
  skills/<nome>/SKILL.md          name: <nome>
  referencias/atual.md            conhecimento volátil (fontes, versões geradas, mudanças a observar)
  templates/                      modelos de código/teste, se houver
```

O `SKILL.md` tem três blocos, nessa ordem (o `fluxo:revisor` procura o último pelo título; `tests/test_marketplace.py` confere):

1. **Implementar** (ou seções por assunto, como `Escrever`, `Modelar`, `Dockerfile`) — como seguir o padrão existente, armadilhas da stack, o que nunca editar.
2. **Testar** (ou `Validar`) — comandos (vindos de `comandos` do perfil), tipos de teste que a stack pede, como validar no ambiente.
3. **Checklist de revisão** — última seção, com pelo menos 5 itens numerados e verificáveis.

Depois:
1. Adicionar o nome a `stacks` no schema (`plugins/fluxo/schema/projeto.schema.json`) e a `STACKS` em `plugins/fluxo/scripts/perfil.py`, e o sinal de detecção na tabela da skill `fluxo:iniciar`.
1. `referencias/atual.md` no formato dos outros (`<!-- dev-flow:conhecimento revisado_em=AAAA-MM-DD produtos=<produto do endoflife.date> -->`, Fontes oficiais, bloco `versoes`, O que acompanhar, Mudanças a observar); padrão de citação do produto em `PADROES` de `scripts/atualizar_conhecimento.py`; rodar o script para gerar a tabela. Stack sem ciclos de suporte publicados (ex.: Bash): `produtos=-`, `## Versões` em texto livre e sem bloco `versoes` (a revisão periódica continua valendo). A skill cita `../../referencias/atual.md` logo após "As convenções do **projeto** vencem".
1. Registrar em `.claude-plugin/marketplace.json` (mesma versão do `plugin.json`).
2. Rodar `python -I scripts/sincronizar_hosts.py` para gerar o espelho Cursor (`.cursor-plugin`).
3. Se a stack tiver validação própria, documentar no `fluxo:validador` (novo `validacao.tipo` exige também `perfil.py` e o schema).
4. Modelo de pipeline em `plugins/azure-pipelines/templates/<nome>.yml` (e no `github-actions`/`gitlab-ci`), se fizer sentido.
5. `claude plugin validate plugins/stack-<nome>` e `python -m unittest discover -s tests`.

Critério para o que entra na skill de stack: vale para **qualquer** projeto daquela stack. O que é de um projeto só vai no `CLAUDE.md` dele.
