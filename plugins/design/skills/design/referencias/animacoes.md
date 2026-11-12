# Animações limpas

Movimento bom passa despercebido: o usuário só sente que a interface é rápida e entende o que aconteceu. Use os tokens de `tokens.css` e os utilitários de `movimento.css` (pasta `templates/` do plugin, `../../../templates/` a partir daqui).

## Tokens
| Token | Valor | Uso |
| --- | --- | --- |
| `--dur-instantanea` | 80ms | cor/opacidade de hover |
| `--dur-rapida` | 120ms | press, toggle, tooltip |
| `--dur-media` | 220ms | dropdown, popover, toast, accordion |
| `--dur-lenta` | 360ms | modal, drawer, troca de tela |
| `--curva-entrada` | `cubic-bezier(0.16, 1, 0.3, 1)` | algo aparece (começa rápido, assenta suave) |
| `--curva-saida` | `cubic-bezier(0.7, 0, 0.84, 0)` | algo sai (acelera para fora) |
| `--curva-padrao` | `cubic-bezier(0.65, 0, 0.35, 1)` | algo muda de lugar/estado na tela |
| `--curva-mola` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | overshoot leve; só em produto "amigável" e em elementos pequenos |

Saída ≈ 0,7–0,8 × a entrada. Elementos maiores e que andam mais podem durar mais; nada de interface passa de ~400 ms.

## Padrões

**Hover / press de botão**
```css
.botao { transition: background-color var(--dur-instantanea) linear, transform var(--dur-rapida) var(--curva-padrao); }
.botao:active { transform: scale(0.97); }
```

**Popover / dropdown / menu** — nasce da origem (o gatilho):
```css
.popover { transform-origin: var(--origem, top left); animation: surgir var(--dur-media) var(--curva-entrada); }
@keyframes surgir { from { opacity: 0; transform: translateY(-4px) scale(0.97); } }
```

**Modal** — fundo faz fade, caixa sobe pouco:
```css
.modal-fundo { animation: fade var(--dur-media) var(--curva-entrada); }
.modal { animation: subir var(--dur-lenta) var(--curva-entrada); }
@keyframes subir { from { opacity: 0; transform: translateY(12px) scale(0.98); } }
```

**Drawer / bottom sheet** — desliza do lado de onde vem, 100% do próprio tamanho, `--dur-lenta`.

**Toast** — entra pelo canto (translate 16 px + fade), sai mais rápido; empilhamento anima com `transform`.

**Lista que aparece** (escalonada, máximo ~8 itens):
```css
.item { animation: subir-curto var(--dur-media) var(--curva-entrada) both; animation-delay: calc(var(--i, 0) * 30ms); }
@keyframes subir-curto { from { opacity: 0; transform: translateY(6px); } }
```

**Accordion / altura automática** — evite animar `height`. Use `grid-template-rows: 0fr → 1fr` (anima sem layout caro por quadro) ou `interpolate-size: allow-keywords` onde houver suporte.
```css
.painel { display: grid; grid-template-rows: 0fr; transition: grid-template-rows var(--dur-media) var(--curva-padrao); }
.painel[data-aberto] { grid-template-rows: 1fr; }
.painel > div { overflow: hidden; }
```

**Skeleton** — brilho sutil e lento (1,2–1,6 s), baixo contraste; troca para conteúdo com fade curto, sem salto de layout (o skeleton tem o tamanho do conteúdo).

**Troca de aba / indicador** — o sublinhado desliza com `transform: translateX()` + `scaleX()`, `--dur-media`, `--curva-padrao`.

**Feedback de sucesso** — ícone com escala 0,8→1 em `--curva-mola` + check desenhado com `stroke-dashoffset`; 300 ms no total.

**Transição entre telas** — View Transitions API (`document.startViewTransition`, ou `@view-transition { navigation: auto; }` em MPA) com `view-transition-name` nos elementos compartilhados; crossfade de 200–300 ms como padrão.

**Número que muda** — contador que rola dígitos só em painel de destaque; em tabela, troca direta com leve realce de fundo (`--cor-sutil`) que some em 600 ms.

## Não fazer
- Animar `width`, `height`, `top`, `left`, `margin`, `box-shadow` grande — use `transform`/`opacity` (para sombra, anime a `opacity` de um pseudo-elemento com a sombra final).
- Bounce/elástico em elemento grande, modal ou texto.
- Animação na primeira carga de tudo ao mesmo tempo; parallax e rolagem sequestrada.
- Loop infinito chamando atenção (exceto carregamento real).
- Bloquear clique durante a animação; fazer o usuário esperar.
- `transition: all` (anima o que não devia e custa caro).

## Movimento reduzido (obrigatório)
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 1ms !important; animation-iteration-count: 1 !important; transition-duration: 1ms !important; scroll-behavior: auto !important; }
}
```
Melhor ainda: para entradas, troque deslocamento por fade curto (o modelo `movimento.css` já faz isso). Em JS (Motion/Framer, GSAP), consulte `matchMedia('(prefers-reduced-motion: reduce)')` e use `useReducedMotion()`.

## Bibliotecas
CSS resolve quase tudo. Se o projeto já usa:
- **Motion (Framer Motion)**: `transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}`; `AnimatePresence` para saída; `layout` para mudanças de posição.
- **GSAP**: para sequências longas/timeline de marketing, não para UI de produto.
- **Flutter**: `AnimatedContainer`/`AnimatedSwitcher` com `Curves.easeOutCubic`/`Curves.easeInCubic`; `Hero` para elemento compartilhado.
- **SwiftUI**: `.animation(.snappy(duration: 0.22), value:)`; **Compose**: `animateContentSize()`, `AnimatedVisibility`, `tween(220, easing = FastOutSlowInEasing)`.

## Conferir
No navegador: DevTools → Rendering → "Emulate prefers-reduced-motion"; painel Animations para desacelerar e ver a curva; Performance sem "Layout" a cada quadro durante a animação; 60 fps em mobile médio.
