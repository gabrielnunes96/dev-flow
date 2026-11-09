# Como criar um plugin de stack

Uma stack nova (ex.: `python`, `angular` separado de `front`, `java`) é um plugin pequeno com uma skill. O núcleo `fluxo` a encontra pelo nome em `stacks` do perfil.

```
plugins/stack-<nome>/
  .claude-plugin/plugin.json      name: stack-<nome>
  skills/<nome>/SKILL.md          name: <nome>
  templates/                      modelos de código/teste, se houver
```

O `SKILL.md` tem três seções, sempre nessa ordem (o `fluxo:revisor` procura a terceira pelo título):

1. **Implementar** — como seguir o padrão existente, armadilhas da stack, o que nunca editar.
2. **Testar** — comandos (vindos de `comandos` do perfil), tipos de teste que a stack pede, como validar no ambiente.
3. **Checklist de revisão** — itens numerados e verificáveis.

Depois:
1. Registrar em `.claude-plugin/marketplace.json`.
2. Se a stack tiver validação própria, documentar no `fluxo:validador` (novo `validacao.tipo` exige também `perfil.py` e o schema).
3. Modelo de pipeline em `plugins/azure-pipelines/templates/<nome>.yml`, se fizer sentido.
4. `claude plugin validate plugins/stack-<nome>` e `python -m unittest discover -s tests`.

Critério para o que entra na skill de stack: vale para **qualquer** projeto daquela stack. O que é de um projeto só vai no `CLAUDE.md` dele.
