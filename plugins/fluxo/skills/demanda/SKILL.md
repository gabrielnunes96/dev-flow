---
name: demanda
description: Transforma uma demanda explicada pelo usuário em especificação funcional (01-funcional.md) com regras de negócio, requisitos, critérios de aceite verificáveis e dúvidas em aberto. Use quando o usuário trouxer uma necessidade nova, um pedido de cliente, um problema a resolver ou pedir uma "funcional".
argument-hint: "[descrição curta ou slug]"
---

# Demanda → especificação funcional

Objetivo: sair com um `01-funcional.md` que outra pessoa leria e entenderia **o que** fazer e **como saber que ficou pronto**, sem decidir o **como** técnico.

## 1. Preparar
- `python -I ../../scripts/perfil.py mostrar` (caminho relativo a esta skill). Sem perfil → sugerir `/fluxo:iniciar` e seguir com `docs/demandas` na raiz.
- Slug: kebab-case curto a partir do pedido (`exportar-chargebacks-csv`). Pasta `{docs}/{slug}/`. Guardar o texto original do usuário em `00-demanda.md` sem editar.

## 2. Entender antes de escrever
- Ler o contexto que já existe: CLAUDE.md, especificações anteriores em `{docs}/`, código que a demanda cita. Não perguntar o que o código responde.
- Perguntar ao usuário só o que muda a especificação e ele precisa decidir — no máximo 4 perguntas por rodada, com opções e uma recomendação (AskUserQuestion). Típicas: quem usa, o que é sucesso, o que fica de fora, regra em caso de conflito, volume/prazo.

## 3. Escrever `01-funcional.md`
- Modelo: `../../templates/01-funcional.md`. Preencher todas as seções; seção sem conteúdo diz "Não se aplica" e por quê.
- Regras com ID (RN-n), requisitos (RF-n) apontando para as regras, critérios (CA-n) em Dado/Quando/Então, **cada um verificável** por teste ou chamada. Critério vago ("rápido", "amigável") vira número ou sai.
- Fora de escopo explícito. Impacto em consumidores existentes.
- Dúvidas que você não conseguiu resolver vão para a seção 10 com para quem perguntar.

## 4. Portão
- Mostrar ao usuário: objetivo, critérios de aceite e dúvidas em aberto (não o documento inteiro).
- Só marcar "aprovada em dd/mm/aaaa" no topo quando o usuário aprovar. Ajustes → nova versão (v2) no mesmo arquivo.
- Aprovada → sugerir `/fluxo:tecnica {slug}`.
