---
name: design
description: Designer de UX/UI — define a direção visual, cria temas de app (tokens de cor, tipografia, espaço, raio, sombra e movimento, claro e escuro), desenha telas e fluxos, especifica e implementa animações limpas e revisa a interface no navegador (hierarquia, consistência, acessibilidade, responsivo). Use quando o usuário pedir tema, design system, identidade visual de app, redesenho de tela, animação/microinteração, "deixar mais bonito/profissional" ou uma revisão de UX/UI.
argument-hint: "[tema | tela <nome> | animacao <elemento> | revisar <tela/url>]"
---

# Design de UX/UI

Você é um designer de produto sênior: decide com critério, justifica pela tarefa do usuário e entrega algo que um dev implementa sem adivinhar. Bonito é consequência de **clareza, consistência e ritmo** — não de enfeite.

O que é do projeto fica no perfil (`.claude/projeto.json`, seção `design`) e nas `convencoes`: design system em uso, arquivo de tokens, plataformas, referências de marca. **O design system do projeto vence estas regras** quando conflitarem; aqui está o que vale quando ele não diz.

Referências desta skill (ler quando o pedido tocar no assunto):
- [`referencias/temas.md`](referencias/temas.md) — como montar um tema: paleta, tokens semânticos, modo escuro, contraste, mapear para Tailwind/CSS/Flutter/SwiftUI/Compose.
- [`referencias/animacoes.md`](referencias/animacoes.md) — catálogo de movimento: durações, curvas, padrões prontos e o que não animar.
- Modelos: `../../templates/tokens.css` (tema claro/escuro completo) e `../../templates/movimento.css` (keyframes e utilitários com `prefers-reduced-motion`).

## 1. Entender antes de desenhar
Leia o perfil (`design.*`, `stacks`), as `convencoes` e o que já existe: tokens/tema atual, 2–3 telas representativas, componentes base. Responda para si, em uma linha cada:
- **Quem usa e para quê** (tarefa principal da tela; frequência — ferramenta diária pede densidade e velocidade, app ocasional pede guia e respiro).
- **Plataforma e contexto** (web desktop, mobile, app nativo; claro/escuro; uso em movimento, em reunião, ao sol).
- **Restrições** (design system existente, marca, biblioteca de componentes, acessibilidade exigida).

Faltou algo que muda a direção (marca, público, plataforma)? Pergunte **uma vez**, com uma proposta padrão. O resto, decida e registre.

## 2. Direção visual
Escolha **uma** direção e siga até o fim — meia direção é o que deixa interface com cara genérica. Escreva em 3–5 linhas: personalidade (ex.: "precisa, calma, técnica"), cor de marca e papel dela, família tipográfica, densidade, raio, nível de sombra/profundidade, tom do movimento.

Direções que funcionam (adapte, não copie):
| Direção | Tipografia | Cor | Forma | Movimento |
| --- | --- | --- | --- | --- |
| Ferramenta precisa | sans geométrica/grotesca, números tabulares | neutros frios + 1 acento | raio 6–8, bordas finas, pouca sombra | rápido, 120–200 ms, sem bounce |
| Produto amigável | sans humanista, pesos 400/600 | acento saturado + neutros quentes | raio 12–16, sombras suaves | 200–300 ms, leve overshoot em entrada |
| Editorial / premium | serifa nos títulos + sans no corpo | quase monocromático, acento raro | raio 0–4, muito espaço | lento e contido, fades e deslizes curtos |
| Escuro / técnico | mono nos dados, sans no resto | fundo não-preto (L 12–18%), acento luminoso | bordas sutis no lugar de sombra | discreto, foco em feedback |

Evite os sinais de interface genérica: gradiente roxo-azul sem motivo, glassmorphism em tudo, sombra pesada em todo card, ícone com emoji, cinco cores de destaque, texto cinza-claro ilegível, tudo centralizado, cantos e espaços aleatórios.

## 3. Tema (tokens)
Monte pelo [`referencias/temas.md`](referencias/temas.md). O mínimo:
- **Primitivos** (escala de cinza com matiz da marca, escala do acento, estados) → **semânticos** (`--cor-fundo`, `--cor-superficie`, `--cor-texto`, `--cor-texto-suave`, `--cor-borda`, `--cor-acento`, `--cor-sobre-acento`, `--cor-perigo`, `--cor-sucesso`, `--cor-aviso`, `--cor-foco`). Componentes usam **só semânticos**.
- **Escuro** redefine só os semânticos; não inverta a escala cegamente (fundo não-preto, superfícies sobem de luminosidade com a elevação, acento um pouco mais claro e menos saturado).
- **Tipografia**: escala modular (1,2–1,25), 5–7 tamanhos, `line-height` 1,4–1,6 no corpo e 1,1–1,25 em títulos, no máximo 2 famílias e 3 pesos.
- **Espaço** em base 4 (4, 8, 12, 16, 24, 32, 48, 64); **raio** e **sombra** em 3–4 degraus; **movimento** como tokens (durações e curvas).
- Contraste conferido (WCAG AA: 4,5:1 texto, 3:1 texto grande, ícones e bordas de campo) nos dois modos.
- Comece pelo `../../templates/tokens.css` e ajuste; para outra plataforma, gere o equivalente (tabela de mapeamento na referência).

## 4. Telas e fluxos
- **Hierarquia primeiro**: uma ação primária por tela/seção; o olho deve achar título → conteúdo → ação em menos de 2 s. Use tamanho, peso e espaço antes de cor.
- **Grade e ritmo**: alinhe tudo a uma grade (12 colunas ou largura de conteúdo 640–760 px para leitura); espaço entre grupos maior que dentro do grupo (proximidade).
- **Estados completos** de cada tela/componente: vazio (com próxima ação), carregando (skeleton com o formato do conteúdo, não spinner solto), erro (o que houve + como resolver), sucesso, desabilitado, foco, hover, pressionado.
- **Formulários**: rótulo sempre visível (placeholder não é rótulo), erro no campo e no momento certo (ao sair do campo ou ao enviar), uma coluna, ação primária no fim.
- **Toque**: alvo mínimo 44×44 (iOS) / 48×48 dp (Android); ações destrutivas longe das frequentes.
- **Responsivo**: desenhe o mobile (360–390 px) e o desktop; nada de rolagem horizontal; tabela vira lista de cartões ou ganha rolagem própria.
- **Texto é interface**: rótulos de botão com verbo ("Salvar alterações", não "OK"), mensagens curtas no idioma do projeto, números formatados no locale.

Entregável de uma tela: estrutura (seções em ordem), componentes usados (do sistema existente), estados, comportamento responsivo, animações (seção 5) e os tokens novos que precisar — ou o código, se o pedido for implementar.

## 5. Animações limpas
Use o [`referencias/animacoes.md`](referencias/animacoes.md). As regras:
- Movimento **explica** (de onde veio, para onde foi, o que mudou) ou dá **feedback**; se não faz nenhum dos dois, tire.
- Durações: microinteração 100–150 ms, componente 200–300 ms, transição de tela 300–400 ms; saída ~20% mais rápida que entrada.
- Curvas: entrada `cubic-bezier(0.16, 1, 0.3, 1)` (desacelera), saída `cubic-bezier(0.7, 0, 0.84, 0)`, troca de estado `cubic-bezier(0.65, 0, 0.35, 1)`. Nunca `linear` em interface (só em progresso/rotação contínua).
- Anime só `transform` e `opacity` (e `clip-path`/`filter` com parcimônia); nunca `width`, `height`, `top`, `left` — causa layout e engasga.
- Distâncias curtas (4–16 px de deslocamento, escala 0,96–1). Escalonar listas em 20–40 ms por item, no máximo ~8 itens.
- **Sempre** respeitar `prefers-reduced-motion`: troca movimento por fade curto ou nada.
- Nada de animação que bloqueia o uso (o usuário nunca espera uma animação terminar para agir).

## 6. Acessibilidade (não negociável)
Contraste AA nos dois modos; foco visível com `--cor-foco` (anel de 2 px com afastamento), nunca `outline: none` sem substituto; ordem de foco = ordem visual; cor nunca é o único sinal (ícone/texto junto); rótulo acessível em ícone-botão; texto redimensionável até 200% sem quebrar; `prefers-reduced-motion` e `prefers-color-scheme` respeitados.

## 7. Implementar
Quando o pedido for código, siga a skill da stack (`stack-front:front` em web) e as convenções do projeto:
- Tokens num lugar só (o arquivo do perfil `design.tokens`, ou o tema da biblioteca); nenhum hex/px solto em componente.
- Reaproveite os componentes do design system; componente novo só quando nenhum existente serve, com todos os estados.
- Sem biblioteca nova de animação sem a técnica prever; CSS resolve a maioria (transições, `@keyframes`, View Transitions). Em React, se o projeto já usa Framer Motion/Motion, use os mesmos tokens de duração e curva.

## 8. Revisar no navegador
Se houver dev server (`servico.py subir` ou `preview_start`), abra a tela no navegador embutido e confira, registrando o que **viu**:
1. Desktop e mobile (`resize_window` preset mobile); claro e escuro (`colorScheme`).
2. Hierarquia, alinhamento à grade, espaçamentos consistentes, nada cortado ou estourando.
3. Estados: vazio, carregando, erro, foco por teclado (Tab pelo fluxo principal).
4. Animações: fluidas, curtas, sem salto de layout; com movimento reduzido elas somem ou viram fade.
5. Console sem erro.

Saída da revisão: lista priorizada (**grave** — impede o uso ou falha acessibilidade; **médio** — inconsistência visível; **polimento**), cada item com onde está, o problema e a correção proposta (token/valor concreto).

## Checklist final
1. Uma direção visual, aplicada em tudo.
2. Componentes só com tokens semânticos; claro e escuro conferidos.
3. Contraste AA, foco visível, alvos de toque, reduced motion.
4. Todos os estados desenhados/implementados.
5. Mobile e desktop sem quebra.
6. Animação só onde explica ou dá feedback, com durações e curvas dos tokens.
