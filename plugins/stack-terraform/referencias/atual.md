# Conhecimento atual: Terraform/OpenTofu
<!-- dev-flow:conhecimento revisado_em=2026-11-19 produtos=terraform -->

> Parte volátil da stack, separada do método (a skill). A tabela de versões é gerada por `scripts/atualizar_conhecimento.py` no repositório do dev-flow; as mudanças a observar entram pela revisão periódica (skill `atualizar-conhecimento`), sempre com aprovação humana. Antes de usar qualquer item, siga o procedimento *projeto primeiro* (`referencias/conhecimento.md` do plugin `fluxo`): a versão do projeto manda.

## Fontes oficiais
- https://github.com/hashicorp/terraform/releases
- https://opentofu.org/docs/intro/whats-new/
- https://endoflife.date/terraform (suporte e fim de vida; fonte da tabela abaixo)

## Versões
<!-- versoes:inicio -->
Gerado em 2026-11-19 por `scripts/atualizar_conhecimento.py` a partir de endoflife.date (ciclos com suporte e os 2 últimos sem suporte). Não editar à mão.

| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| terraform | 1.17 | suportado | 2026-10-21 | — | — | 1.17.2 |
| terraform | 1.16 | suportado | 2026-08-26 | — | — | 1.16.7 |
| terraform | 1.15 | sem suporte | 2026-04-29 | — | 2026-10-21 | 1.15.9 |
| terraform | 1.14 | sem suporte | 2025-11-19 | — | 2026-08-26 | 1.14.9 |
<!-- versoes:fim -->

## O que acompanhar
- `required_version` e versões dos providers fixadas; fim de suporte da CLI.
- Mudanças de licença/ferramenta (Terraform × OpenTofu) seguem a decisão do projeto.

## Mudanças a observar
Nenhuma registrada ainda. Cada item entra com data, fonte e a partir de que versão vale.
