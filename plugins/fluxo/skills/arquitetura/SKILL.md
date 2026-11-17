---
name: arquitetura
description: Registra e avalia decisões de arquitetura — gera ADRs (registro de decisão) com alternativas e trade-offs, descreve a arquitetura atual do sistema (contexto, containers, componentes em texto), e audita um sistema contra requisitos de qualidade (escalabilidade, resiliência, segurança, observabilidade, custo). Use quando o usuário pedir uma ADR, "documenta a arquitetura", "qual a melhor abordagem para X", uma revisão arquitetural ou ao surgir uma decisão estrutural fora de uma técnica.
argument-hint: "[adr <decisão> | mapa | revisar]"
---

# Arquitetura

Método: `../../referencias/raciocinio.md` (seções 1, 4 e 7), relativo a esta skill. Modelo de ADR: `../../templates/adr.md`.

Onde gravar: `docs/adr/` na raiz do projeto, se existir ou se o projeto versiona `docs`; senão `{docs}/adr/`. Numeração sequencial `NNNN-titulo-em-kebab.md` (ler a última existente). ADR aceita não se edita: uma nova a **substitui** (`Substitui: 0007`, e a antiga ganha `Substituída por: 0012`).

## adr `<decisão>`
1. Contexto: requisito que força a decisão (com número quando houver), restrições, o que existe hoje (ler código e ADRs anteriores).
2. Delegar ao subagente `fluxo:arquiteto` com a decisão e o contexto. Ele devolve alternativas, trade-offs e recomendação.
3. Escrever a ADR com situação **proposta**. Mostrar ao usuário: opções, recomendação, consequências. A escolha é dele quando envolve custo, prazo ou produto.
4. Aprovada → situação **aceita em dd/mm/aaaa**. Se nasceu de uma demanda, citar a ADR na seção 9 da `02-tecnica.md`.

## mapa
Descrever a arquitetura atual em `docs/arquitetura.md` (ou atualizar a existente):
- **Contexto**: o sistema, quem usa, com que sistemas externos conversa.
- **Containers**: aplicações, bancos, filas, caches — com tecnologia e como se comunicam (protocolo, síncrono/assíncrono).
- **Componentes** dos containers principais: camadas/módulos e responsabilidades, com caminho no repositório.
- **Fluxos críticos**: 2–3 caminhos do dado mais importantes, ponta a ponta.
- **Operação**: onde roda (`infra` do perfil), como é implantado (`ci` do perfil), como é observado.
Diagramas em texto (bloco `text` com setas), sem mermaid. Tudo verificado no código: o subagente `fluxo:analista` levanta, você escreve.

## revisar
1. Requisitos de qualidade: perguntar ao usuário os que não estão escritos (volume, latência, disponibilidade, RPO/RTO).
2. Subagente `fluxo:arquiteto` (estrutura, resiliência, escalabilidade, custo) e `fluxo:seguranca` em modo ameaças, em paralelo.
3. Relatório `docs/revisao-arquitetura-<data>.md`: achados por severidade com evidência, riscos, e recomendações ordenadas por valor/esforço. Cada recomendação estrutural vira uma ADR proposta ou uma demanda (`/fluxo:demanda`).
