# Montar um tema

Um tema é um conjunto pequeno de decisões aplicadas com disciplina. Ordem: **paleta → semânticos → tipografia → espaço/forma → movimento → conferir contraste**.

## 1. Paleta (primitivos)
Use **OKLCH** (`oklch(L C H)`): a luminosidade (L) é perceptual, então degraus com o mesmo L têm o mesmo "peso" em matizes diferentes e o contraste fica previsível. Ofereça fallback hex só se o projeto suportar navegadores antigos.

- **Neutros**: 11–12 degraus (L de ~99% a ~13%) com croma baixo (0,005–0,02) **no matiz da marca** — cinza "com a temperatura" da marca fica mais refinado que cinza puro.
- **Acento** (marca): 1 cor, 10–12 degraus. O degrau principal fica em L ~55–65% e C ~0,15–0,2. Uma segunda cor de destaque só se tiver papel próprio.
- **Estados**: perigo (H ~25), aviso (H ~75), sucesso (H ~150), info (H ~250); 3 degraus cada (fundo suave, borda/ícone, texto) bastam.

Gere escalas variando L em passos quase iguais e reduzindo C nos extremos (cores muito claras ou escuras saturadas ficam "sujas" ou fora do gamut).

## 2. Tokens semânticos
Componentes **nunca** usam primitivos. Nomeie pelo papel, não pela cor:

| Token | Papel | Claro (ex.) | Escuro (ex.) |
| --- | --- | --- | --- |
| `--cor-fundo` | fundo da página | neutro 99% | neutro 14% |
| `--cor-superficie` | cartão, painel | branco | neutro 18% |
| `--cor-superficie-2` | elevado (menu, modal) | branco | neutro 22% |
| `--cor-sutil` | fundo de hover, área agrupada | neutro 96% | neutro 24% |
| `--cor-borda` | divisória, contorno | neutro 90% | neutro 30% |
| `--cor-borda-forte` | campo de formulário | neutro 75% | neutro 42% |
| `--cor-texto` | texto principal | neutro 20% | neutro 94% |
| `--cor-texto-suave` | secundário, legenda | neutro 45% | neutro 70% |
| `--cor-acento` | ação primária, link | acento 55% | acento 70% |
| `--cor-acento-hover` | hover da primária | acento 48% | acento 76% |
| `--cor-sobre-acento` | texto sobre o acento | branco | neutro 12% |
| `--cor-foco` | anel de foco | acento 60% | acento 72% |
| `--cor-perigo` / `-sucesso` / `-aviso` | estados | — | — |

No escuro:
- Fundo **não** é `#000` (cansa e "vaza" no OLED com rolagem); use L 12–18%.
- Elevação = superfície mais clara (não sombra, que some no escuro).
- Acento sobe a luminosidade e perde um pouco de croma para não vibrar.
- Texto principal não é branco puro (L ~92–95%).
- Imagens e ilustrações podem precisar de `filter: brightness(.9)` ou versão própria.

Troca de modo: `@media (prefers-color-scheme: dark)` como padrão **e** atributo `[data-tema="escuro"]`/`[data-tema="claro"]` para escolha manual. Aplique o tema antes da primeira pintura (script inline no `<head>`) para não piscar.

## 3. Tipografia
- No máximo 2 famílias (uma pode ser a do sistema: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`). Fonte web: `font-display: swap`, subconjunto latino, 2–3 pesos.
- Escala modular com razão 1,2 (interfaces densas) ou 1,25 (mais respiro). Base 16 px (14–15 em ferramentas muito densas).
  - 1,25: 12 · 14 · 16 · 20 · 25 · 31 · 39
- `line-height`: corpo 1,5; títulos 1,15–1,25; `letter-spacing` levemente negativo (-0,01 a -0,02em) em títulos grandes, positivo em caixa alta pequena.
- Números em tabela/painel: `font-variant-numeric: tabular-nums`.
- Comprimento de linha de leitura: 60–75 caracteres (`max-width: 65ch`).

## 4. Espaço, forma e profundidade
- Espaço em base 4: `4 8 12 16 24 32 48 64 96`. Dentro de um componente use os pequenos; entre seções, os grandes. Mesmo papel = mesmo valor.
- Raio: 3 degraus (`--raio-p` 4–6, `--raio-m` 8–12, `--raio-g` 16–24) + `--raio-total` 999 px. Raio interno = raio externo − espaçamento.
- Sombra: 3 níveis com duas camadas (uma curta e definida, uma longa e difusa) e cor do matiz do neutro com alfa baixo. Em escuro, troque por borda clara sutil.
- Bordas finas (1 px) com `--cor-borda` organizam melhor que sombra em interfaces densas.

## 5. Movimento como token
`--dur-rapida 120ms`, `--dur-media 220ms`, `--dur-lenta 360ms`; `--curva-entrada`, `--curva-saida`, `--curva-padrao`. Detalhes em [`animacoes.md`](animacoes.md).

## 6. Conferir contraste
Calcule a razão WCAG para cada par usado (texto/fundo, texto/superfície, texto-suave/superfície, sobre-acento/acento, borda-forte/fundo, foco/fundo) **nos dois modos**. Mínimos: 4,5:1 texto normal; 3:1 texto ≥ 24 px (ou 19 px negrito), ícones, bordas de campo e anel de foco. Ajuste o L do token, não a opacidade.

Conta rápida (luminância relativa): converta sRGB para linear (`c ≤ 0,04045 ? c/12,92 : ((c+0,055)/1,055)^2,4`), `L = 0,2126R + 0,7152G + 0,0722B`, razão = `(L1 + 0,05)/(L2 + 0,05)`. Para OKLCH, converta para sRGB antes (ou confira no DevTools, que mostra a razão no seletor de cor).

## 7. Mapear para a plataforma
| Plataforma | Onde ficam os tokens |
| --- | --- |
| CSS puro | `:root` + `[data-tema]` (modelo `tokens.css`) |
| Tailwind v4 | `@theme { --color-acento: var(--cor-acento); … }` apontando para os semânticos; escuro via `@custom-variant dark` |
| Tailwind v3 | `theme.extend.colors.acento = 'rgb(var(--cor-acento-rgb) / <alpha-value>)'`, `darkMode: ['class', '[data-tema="escuro"]']` |
| shadcn/ui | as variáveis `--background`, `--foreground`, `--primary`… recebem os semânticos |
| MUI | `createTheme({ palette: { mode, primary, background, text }, shape, typography, transitions })` |
| Flutter | `ThemeData(colorScheme: ColorScheme(...), textTheme, extensions: [Tokens])` com tema claro e escuro |
| SwiftUI | Asset Catalog com cores "Any/Dark" + `extension Color`/`Font` |
| Jetpack Compose | `lightColorScheme`/`darkColorScheme` + `MaterialTheme(typography, shapes)` |

## Entregável de um tema
1. A direção em 3–5 linhas.
2. O arquivo de tokens (claro e escuro) no formato da plataforma.
3. A tabela de contraste dos pares principais nos dois modos.
4. Uma amostra: página com tipografia, botões (todos os estados), campo, cartão, alerta, tabela — em claro e escuro — para conferência visual.
