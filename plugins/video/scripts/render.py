"""Vídeo-resumo animado (1080p, 30 fps) a partir de um roteiro JSON e das falas voz_<id>.wav da mesma pasta.

Uso: python -I render.py <roteiro.json> folha [saida.png]     (um quadro do fim de cada cena, numa folha)
     python -I render.py <roteiro.json> previa <s> [<s> ...]  (quadros soltos em previa_<s>.png)
     python -I render.py <roteiro.json> video <saida.mp4>

Dependências: Pillow, numpy e imageio-ffmpeg (requirements.txt). Fontes Segoe UI/Consolas do Windows; em outro
sistema, defina "fontes" no roteiro com caminhos .ttf.
"""
import math
import os
import random
import subprocess
import sys
import wave
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roteiro as rot  # noqa: E402

try:
    import imageio_ffmpeg
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError as e:
    sys.exit(f"dependência ausente ({e.name}): pip install -r requirements.txt")

W, H, FPS, SR = 1920, 1080, 30, 44100
X = 140
WHITE, MUTED = (255, 255, 255), (160, 178, 204)
GREEN, RED, AMBER, BLUE = (62, 207, 130), (235, 87, 87), (250, 190, 70), (70, 140, 230)
TEMA = {"fundo_claro": (26, 52, 94), "fundo_escuro": (5, 13, 28), "destaque": (245, 140, 40)}
FONTES = {"black": "C:/Windows/Fonts/seguibl.ttf", "bold": "C:/Windows/Fonts/segoeuib.ttf", "reg": "C:/Windows/Fonts/segoeui.ttf",
          "mono": "C:/Windows/Fonts/consola.ttf", "monob": "C:/Windows/Fonts/consolab.ttf"}


def cor(nome):
    return tuple(TEMA[nome])


@lru_cache(None)
def fnt(k, s):
    p = FONTES[k]
    if not os.path.exists(p):
        p = FONTES["bold"] if os.path.exists(FONTES["bold"]) else None
    return ImageFont.truetype(p, s) if p else ImageFont.load_default(s)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3


def ease_io(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)


def prog(t, t0, d=0.6):
    return ease((t - t0) / d)


def rgba(c, a):
    return (c[0], c[1], c[2], int(255 * clamp(a)))


def el(v):
    """Elemento de texto: 'texto' ou {"texto": ..., "quando": ...} -> (texto, quando)."""
    if v is None:
        return None, None
    if isinstance(v, str):
        return v, None
    return v.get("texto"), v.get("quando")


# ---------- texto com alfa (o text() do Pillow ignora o alfa da cor numa imagem RGB) ----------
@lru_cache(maxsize=8192)
def _mascara(txt, font, anchor):
    l, t, r, b = font.getbbox(txt, anchor=anchor)
    m = Image.new("L", (r - l + 4, b - t + 4), 0)
    ImageDraw.Draw(m).text((-l + 2, -t + 2), txt, font=font, fill=255, anchor=anchor)
    return m, l - 2, t - 2


class Pincel:
    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")

    def __getattr__(self, nome):
        return getattr(self.d, nome)

    def text(self, xy, txt, font, fill, anchor="la"):
        a = fill[3] if len(fill) == 4 else 255
        if a <= 0 or not txt:
            return
        m, ox, oy = _mascara(txt, font, anchor)
        if a < 255:
            m = m.point(lambda v, a=a: v * a // 255)
        self.img.paste(tuple(fill[:3]), (int(round(xy[0] + ox)), int(round(xy[1] + oy))), m)


# ---------- fundo ----------
class Fundo:
    def __init__(self):
        y = np.linspace(0, 1, H)[:, None]
        x = np.linspace(0, 1, W)[None, :]
        m = np.clip(0.75 * y + 0.35 * x, 0, 1)
        arr = np.array(cor("fundo_claro"))[None, None, :] * (1 - m[..., None]) + np.array(cor("fundo_escuro"))[None, None, :] * m[..., None]
        self.base = Image.fromarray(arr.astype(np.uint8), "RGB")
        d = ImageDraw.Draw(self.base, "RGBA")
        for gx in range(0, W, 80):
            d.line((gx, 0, gx, H), fill=(255, 255, 255, 7))
        for gy in range(0, H, 80):
            d.line((0, gy, W, gy), fill=(255, 255, 255, 7))
        yy = np.linspace(-1, 1, H)[:, None]
        xx = np.linspace(-1, 1, W)[None, :]
        self.vinheta = Image.fromarray((np.clip((np.sqrt(xx * xx * 0.8 + yy * yy) - 0.55) / 0.9, 0, 1) * 190).astype(np.uint8), "L")
        self.preto = Image.new("RGB", (W, H), (0, 0, 0))
        self.blobs = [self._blob(cor("destaque"), 900, 0.20), self._blob(BLUE, 1100, 0.30)]
        rnd = random.Random(7)
        self.part = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(8, 30), rnd.uniform(1.2, 3.2), rnd.uniform(0.08, 0.3))
                     for _ in range(70)]

    @staticmethod
    def _blob(c, tam, alfa):
        m = Image.new("L", (tam, tam), 0)
        ImageDraw.Draw(m).ellipse((tam * 0.2, tam * 0.2, tam * 0.8, tam * 0.8), fill=int(255 * alfa))
        return Image.new("RGB", (tam, tam), c), m.filter(ImageFilter.GaussianBlur(tam * 0.12))

    def quadro(self, gt):
        f = self.base.copy()
        (bo, mo), (bb, mb) = self.blobs
        f.paste(bo, (int(1150 + 180 * math.sin(gt * 0.13)), int(-260 + 120 * math.cos(gt * 0.11))), mo)
        f.paste(bb, (int(-320 + 160 * math.cos(gt * 0.09)), int(420 + 130 * math.sin(gt * 0.12))), mb)
        d = ImageDraw.Draw(f, "RGBA")
        for x, y0, sp, sz, al in self.part:
            y = (y0 - sp * gt) % (H + 40) - 20
            xx = x + 12 * math.sin(gt * 0.5 + y0)
            d.ellipse((xx - sz, y - sz, xx + sz, y + sz), fill=rgba(WHITE, al))
        return f


# ---------- primitivas ----------
def card(d, box, a, c=WHITE, fa=0.06, oa=0.18, r=18, w=2):
    d.rounded_rectangle(box, radius=r, fill=rgba(c, fa * a), outline=rgba(c, oa * a), width=w)


def pill(d, cx, cy, texto, fk, tam, c, a, cheio=False, pad=30):
    if a <= 0 or not texto:
        return
    f = fnt(fk, tam)
    tw = d.textlength(texto, font=f)
    h = tam + 30
    d.rounded_rectangle((cx - tw / 2 - pad, cy - h / 2, cx + tw / 2 + pad, cy + h / 2), radius=h / 2,
                        fill=rgba(c, (0.95 if cheio else 0.10) * a), outline=rgba(c, a), width=2)
    d.text((cx, cy), texto, font=f, fill=rgba(cor("fundo_escuro") if cheio else c, a), anchor="mm")


def linha_parcial(d, pts, p, c, a, w):
    if p <= 0 or a <= 0:
        return None, 0.0
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    falta = sum(math.dist(s, e) for s, e in segs) * clamp(p)
    ponta, ang = pts[0], 0.0
    for s, e in segs:
        L = math.dist(s, e)
        if L == 0:
            continue
        k = min(1, falta / L)
        ponta = (s[0] + (e[0] - s[0]) * k, s[1] + (e[1] - s[1]) * k)
        ang = math.atan2(e[1] - s[1], e[0] - s[0])
        d.line((s, ponta), fill=rgba(c, a), width=w, joint="curve")
        falta -= L
        if falta <= 0:
            break
    return ponta, ang


def seta(d, pts, p, c, a, w=4):
    ponta, ang = linha_parcial(d, pts, p, c, a, w)
    if ponta and p >= 0.98:
        hx, hy = ponta
        s = 16
        d.polygon([(hx, hy), (hx - s * math.cos(ang - 0.45), hy - s * math.sin(ang - 0.45)),
                   (hx - s * math.cos(ang + 0.45), hy - s * math.sin(ang + 0.45))], fill=rgba(c, a))


def check(d, cx, cy, r, p, c=GREEN, a=1.0):
    if p <= 0:
        return
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(c, 0.18 * a), outline=rgba(c, a), width=3)
    linha_parcial(d, [(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.12, cy + r * 0.35), (cx + r * 0.5, cy - r * 0.35)], p, c, a,
                  max(3, int(r * 0.16)))


def caixa(d, box, titulo, sub, a, tipo=None, dy=0.0):
    if a <= 0:
        return
    x0, y0, x1, y1 = box
    y0, y1 = y0 + dy, y1 + dy
    c = {"ruim": RED, "destaque": cor("destaque")}.get(tipo, WHITE)
    d.rounded_rectangle((x0, y0, x1, y1), radius=16, fill=rgba(c, (0.16 if tipo else 0.06) * a),
                        outline=rgba(c, (1.0 if tipo else 0.25) * a), width=3 if tipo else 2)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if sub:
        d.text((cx, cy - 15), titulo, font=fnt("bold", 30), fill=rgba(WHITE, a), anchor="mm")
        d.text((cx, cy + 22), sub, font=fnt("reg", 22), fill=rgba(WHITE if tipo else MUTED, a), anchor="mm")
    else:
        d.text((cx, cy), titulo, font=fnt("bold", 30), fill=rgba(WHITE, a), anchor="mm")


def cabecalho(d, c, t):
    p = prog(t, 0.15, 0.7)
    d.text((X, 92 + (1 - p) * 20), f"{c['idx']:02d}   {c.get('capitulo', '').upper()}", font=fnt("bold", 26),
           fill=rgba(cor("destaque"), p))
    p2 = prog(t, 0.3, 0.8)
    d.text((X, 128 + (1 - p2) * 30), c["titulo"], font=fnt("black", 66), fill=rgba(WHITE, p2))
    p3 = ease_io((t - 0.55) / 0.8)
    if p3 > 0:
        d.rectangle((X, 236, X + 140 * p3, 242), fill=cor("destaque"))


def conta(n, t, t0, dur=1.3):
    return int(round(n * ease_io((t - t0) / dur)))


def fmt_num(v, n):
    return str(n) if isinstance(v, int) else v


def digitando(d, xy, texto, t, t0, dur, fonte, c, a=1.0):
    n = int(len(texto) * clamp((t - t0) / dur))
    cursor = "▌" if n < len(texto) and (t * 2) % 1 < 0.5 else ""
    d.text(xy, texto[:n] + cursor, font=fonte, fill=rgba(c, a), anchor="lm")


A = rot.at  # A(cena, quando, padrao) -> segundos na cena


# ---------- cenas ----------
def c_abertura(f, d, c, t):
    cx = W / 2
    p0 = prog(t, 0.15, 0.8)
    pill(d, cx, 300 - (1 - p0) * 20, c.get("etiqueta"), "bold", 24, cor("destaque"), p0)
    p1 = prog(t, 0.45, 0.9)
    d.text((cx, 445 + (1 - p1) * 50), c["titulo"], font=fnt("black", 100), fill=rgba(WHITE, p1), anchor="mm")
    lw = 760 * ease_io((t - 0.35) / 1.1)
    if lw > 0:
        d.rectangle((cx - lw / 2, 548, cx + lw / 2, 555), fill=cor("destaque"))
    p2 = prog(t, 0.85, 0.9)
    d.text((cx, 650 + (1 - p2) * 50), c.get("destaque", ""), font=fnt("black", 100), fill=rgba(cor("destaque"), p2), anchor="mm")
    p3 = prog(t, 1.6, 0.9)
    d.text((cx, 790), c.get("subtitulo", ""), font=fnt("reg", 32), fill=rgba(MUTED, p3), anchor="mm")


def c_manchete(f, d, c, t):
    cx, cy, r = W / 2, 320, 118
    pa = ease_io((t - 0.3) / 0.9)
    if pa > 0:
        d.ellipse((cx - r - 30, cy - r - 30, cx + r + 30, cy + r + 30), fill=rgba(GREEN, (0.10 + 0.05 * math.sin(t * 3)) * pa))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(GREEN, 0.14 * pa))
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * pa, fill=rgba(GREEN, 1), width=12)
    linha_parcial(d, [(cx - 52, cy + 4), (cx - 14, cy + 44), (cx + 58, cy - 38)], (t - 1.05) / 0.45, GREEN, 1, 16)
    tx, q = el(c["titulo"])
    p = prog(t, A(c, q, 1.0), 0.7)
    d.text((cx, 555 + (1 - p) * 40), tx, font=fnt("black", 100), fill=rgba(WHITE, p), anchor="mm")
    tx, q = el(c.get("subtitulo"))
    p = prog(t, A(c, q, 1.6), 0.7)
    d.text((cx, 655 + (1 - p) * 30), tx or "", font=fnt("reg", 42), fill=rgba(MUTED, p), anchor="mm")
    tx, q = el(c.get("selo"))
    pill(d, cx, 755, tx, "bold", 32, cor("destaque"), prog(t, A(c, q, 2.2), 0.7))
    pr = c.get("progresso")
    if pr:
        t4 = A(c, pr.get("quando"), 2.8)
        p = prog(t, t4, 0.6)
        if p > 0:
            x0, x1, y = cx - 460, cx + 460, 880
            d.text((x0, y - 34), f"{conta(pr['feito'], t, t4 + 0.2, 1.4)} de {pr['total']} {pr.get('rotulo', '')}",
                   font=fnt("bold", 30), fill=rgba(WHITE, p), anchor="ls")
            d.text((x1, y - 34), pr.get("obs", ""), font=fnt("reg", 26), fill=rgba(AMBER, p), anchor="rs")
            d.rounded_rectangle((x0, y, x1, y + 18), radius=9, fill=rgba(WHITE, 0.12 * p))
            q = ease_io((t - t4 - 0.2) / 1.4) * pr["feito"] / pr["total"]
            if q > 0:
                d.rounded_rectangle((x0, y, x0 + (x1 - x0) * q, y + 18), radius=9, fill=rgba(GREEN, p))


def _layout(lado, x0, x1):
    caixas = {}
    linhas = []
    for i, camada in enumerate(lado["camadas"]):
        n = len(camada)
        w = (x1 - x0 - 60 * (n - 1)) / n
        y = 340 + i * 170
        lin = []
        for j, b in enumerate(camada):
            bid = b.get("id", f"{i}_{j}")
            caixas[bid] = dict(b, box=(x0 + j * (w + 60), y, x0 + j * (w + 60) + w, y + 96), linha=i)
            lin.append(bid)
        linhas.append(lin)
    setas = []
    for i in range(1, len(linhas)):
        cima, baixo = linhas[i - 1], linhas[i]
        ligados = set()
        for u in cima:
            ub = caixas[u]["box"]
            for b in baixo:
                lb = caixas[b]["box"]
                lo, hi = max(ub[0], lb[0]), min(ub[2], lb[2])
                if hi > lo:
                    xm = (lo + hi) / 2
                    setas.append({"pts": [(xm, ub[3]), (xm, lb[1])], "para": b})
                    ligados.add(b)
    for s in lado.get("setas_extra", []):
        ub, lb = caixas[s["de"]]["box"], caixas[s["para"]]["box"]
        direita = (lb[0] + lb[2]) > (ub[0] + ub[2])
        xs = ub[2] - 60 if direita else ub[0] + 60
        xe = lb[0] + (lb[2] - lb[0]) * 0.3 if direita else lb[2] - (lb[2] - lb[0]) * 0.3
        ym = ub[3] + 35
        setas.append({"pts": [(xs, ub[3]), (xs, ym), (xe, ym), (xe, lb[1])], "para": s["para"], "rotulo": s.get("rotulo"),
                      "meio": ((xs + xe) / 2, ym + 18)})
    return caixas, setas


def c_antes_depois(f, d, c, t):
    cabecalho(d, c, t)
    t_antes = A(c, c["antes"].get("quando"), 0.7)
    t_agora = A(c, c["agora"].get("quando"), c["voz"] * 0.5)
    for nome, x0, x1, ativo in (("antes", 140, 900, False), ("agora", 1020, 1780, True)):
        lado = c[nome]
        t0 = t_antes if nome == "antes" else t_agora
        dim = 1.0 if ativo else 1 - 0.55 * prog(t, t_agora, 0.8)
        cor_seta = cor("destaque") if ativo else MUTED
        p = prog(t, t0, 0.6)
        d.text((x0, 300), lado.get("rotulo", nome.upper()), font=fnt("bold", 26),
               fill=rgba(cor("destaque") if ativo else MUTED, p * dim))
        caixas, setas = _layout(lado, x0, x1)
        tempo = {k: A(c, b.get("quando"), t0) for k, b in caixas.items()}
        for s in setas:
            tk = tempo[s["para"]]
            seta(d, s["pts"], (t - tk + 0.2) / 0.5, cor_seta, dim)
            if s.get("rotulo"):
                d.text(s["meio"], s["rotulo"], font=fnt("reg", 20), fill=rgba(MUTED, prog(t, tk, 0.6) * dim), anchor="mm")
        for k, b in caixas.items():
            pk = prog(t, tempo[k], 0.6)
            caixa(d, b["box"], b["titulo"], b.get("sub"), pk * dim, b.get("tipo"), (1 - pk) * 20)
        tx, q = el(lado.get("nota"))
        if tx:
            ultimo = max(b["box"][3] for b in caixas.values())
            d.text(((x0 + x1) / 2, ultimo + 60), tx, font=fnt("reg", 26), fill=rgba(MUTED, prog(t, A(c, q, t0 + 2), 0.6) * dim),
                   anchor="mm")
        if nome == "antes":
            for k in c.get("riscar", []):
                x_0, y_0, x_1, y_1 = caixas[k]["box"]
                linha_parcial(d, [(x_0 + 30, y_0 + 15), (x_1 - 30, y_1 - 15)], ease_io((t - t_agora - 0.3) / 0.5), RED, 1, 6)
                linha_parcial(d, [(x_1 - 30, y_0 + 15), (x_0 + 30, y_1 - 15)], ease_io((t - t_agora - 0.6) / 0.5), RED, 1, 6)
    d.line((960, 300, 960, 800), fill=rgba(WHITE, 0.12 * prog(t, t_antes, 0.6)), width=2)


def c_numeros(f, d, c, t):
    cabecalho(d, c, t)
    cartoes = c["cartoes"]
    n = len(cartoes)
    cw = (1640 - 60 * (n - 1)) / n
    tam = 110 if cw > 700 else 84
    for i, k in enumerate(cartoes):
        x0, y0 = 140 + i * (cw + 60), 290
        x1, y1 = x0 + cw, 830
        t0 = A(c, k.get("quando"), 0.8 + i * 2)
        p = prog(t, t0, 0.7)
        if p <= 0:
            continue
        dy = (1 - p) * 40
        card(d, (x0, y0 + dy, x1, y1 + dy), p, fa=0.07, oa=0.2)
        d.rectangle((x0, y0 + dy, x1, y0 + dy + 6), fill=rgba(cor("destaque"), p))
        d.text((x0 + 44, y0 + 60 + dy), k["titulo"], font=fnt("bold", 38), fill=rgba(WHITE, p), anchor="lm")
        d.text((x0 + 44, y0 + 108 + dy), k.get("sub", ""), font=fnt("reg", 26), fill=rgba(MUTED, p), anchor="lm")
        stats = k.get("stats", [])
        sw = cw / max(1, len(stats))
        for j, s in enumerate(stats):
            tk = A(c, s.get("quando"), t0 + 0.4 * j) - 0.2
            pk = prog(t, tk, 0.5)
            cx = x0 + sw * (j + 0.5)
            if j:
                d.line((x0 + sw * j, y0 + 200 + dy, x0 + sw * j, y0 + 440 + dy), fill=rgba(WHITE, 0.12 * p), width=2)
            v = s["valor"]
            txt = str(conta(v, t, tk, 1.1)) if isinstance(v, int) else str(v)
            d.text((cx, y0 + 290 + dy), txt, font=fnt("black", tam), fill=rgba(cor("destaque"), pk), anchor="mm")
            d.text((cx, y0 + 385 + dy), s.get("rotulo", ""), font=fnt("reg", 28), fill=rgba(WHITE, pk), anchor="mm")
        tx, q = el(k.get("selo"))
        if tx:
            pill(d, x0 + sw * (len(stats) - 0.5), 760, tx, "bold", 24, AMBER, prog(t, A(c, q, t0 + 2), 0.5))
    tx, q = el(c.get("nota"))
    if tx:
        d.text((W / 2, 900), tx, font=fnt("reg", 26), fill=rgba(MUTED, prog(t, A(c, q, c["voz"]), 0.6)), anchor="mm")


def c_lista(f, d, c, t):
    cabecalho(d, c, t)
    tx, q = el(c.get("digitando"))
    if tx:
        t0 = A(c, q, 0.9)
        pr = prog(t, t0, 0.5)
        if pr > 0:
            fm = fnt("mono", 30)
            largura = d.textlength(tx, font=fm) + 60
            bx = (1780 - largura, 150, 1780, 214)
            d.rounded_rectangle(bx, radius=12, fill=rgba(cor("fundo_escuro"), 0.85 * pr), outline=rgba(cor("destaque"), 0.6 * pr), width=2)
            digitando(d, (bx[0] + 26, 182), tx, t, t0 + 0.1, 1.3, fm, WHITE, pr)
    itens = c["itens"]
    passo = min(150, 640 / len(itens))
    for i, it in enumerate(itens):
        p = prog(t, A(c, it.get("quando"), 0.8 + i * 1.5) - 0.15, 0.7)
        if p <= 0:
            continue
        y0 = 300 + i * passo
        dx = (1 - p) * 80
        card(d, (140 + dx, y0, 1780 + dx, y0 + passo - 24), p)
        cy = y0 + (passo - 24) / 2
        d.ellipse((190 + dx, cy - 38, 266 + dx, cy + 38), fill=rgba(cor("destaque"), 0.16 * p), outline=rgba(cor("destaque"), p), width=3)
        d.text((228 + dx, cy), str(i + 1), font=fnt("black", 36), fill=rgba(cor("destaque"), p), anchor="mm")
        d.text((300 + dx, cy - 22), it["titulo"], font=fnt("bold", 36), fill=rgba(WHITE, p), anchor="lm")
        d.text((300 + dx, cy + 26), it.get("detalhe", ""), font=fnt("reg", 26), fill=rgba(MUTED, p), anchor="lm")


def c_grade(f, d, c, t):
    cabecalho(d, c, t)
    tx, q = el(c.get("intro"))
    if tx:
        p = prog(t, A(c, q, 0.8), 0.6)
        f1 = fnt("bold", 34)
        d.text((X, 285), tx + " ", font=f1, fill=rgba(WHITE, p), anchor="lm")
        d.text((X + d.textlength(tx + " ", font=f1), 285), c.get("intro_destaque", ""), font=f1, fill=rgba(cor("destaque"), p), anchor="lm")
    itens = c["itens"]
    cols = 4 if len(itens) > 6 else 3
    cw = (1640 - 24 * (cols - 1)) / cols
    for i, it in enumerate(itens):
        tk = A(c, it.get("quando"), 1.0 + i * 0.8) - 0.1
        p = prog(t, tk, 0.45)
        if p <= 0:
            continue
        x0, y0 = 140 + (i % cols) * (cw + 24), 350 + (i // cols) * 140
        dy = (1 - p) * 30
        brilho = clamp(1 - (t - tk) / 1.2)
        d.rounded_rectangle((x0, y0 + dy, x0 + cw, y0 + 120 + dy), radius=16, fill=rgba(WHITE, (0.06 + 0.08 * brilho) * p),
                            outline=rgba(cor("destaque") if brilho > 0 else WHITE, (0.25 + 0.75 * brilho) * p), width=2)
        d.text((x0 + 26, y0 + 44 + dy), it["nome"], font=fnt("bold", 28), fill=rgba(WHITE, p), anchor="lm")
        d.text((x0 + 26, y0 + 86 + dy), it.get("sub", ""), font=fnt("mono", 21), fill=rgba(MUTED, p), anchor="lm")
        check(d, x0 + cw - 42, y0 + 44 + dy, 20, (t - tk - 0.25) / 0.4, GREEN, p)
    selos = c.get("selos", [])
    for i, s in enumerate(selos):
        tx, q = el(s)
        cx = W / 2 if len(selos) == 1 else (560 if i == 0 else 1360)
        pill(d, cx, 820, tx, "bold", 28, cor("destaque") if i == 0 else WHITE, prog(t, A(c, q, c["voz"] * 0.8), 0.6))


def c_aneis(f, d, c, t):
    cabecalho(d, c, t)
    aneis = c["aneis"]
    n = len(aneis)
    xs = [960] if n == 1 else [560, 1360] if n == 2 else [440, 960, 1480]
    for (cx, a) in zip(xs, aneis):
        t0 = A(c, a.get("quando"), 0.8)
        p = prog(t, t0, 0.6)
        if p <= 0:
            continue
        cy = 560
        d.text((cx, 330), a["titulo"], font=fnt("bold", 34), fill=rgba(WHITE, p), anchor="mm")
        r = 175 if n < 3 else 150
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(WHITE, 0.10 * p), width=22)
        q = ease_io((t - t0 - 0.2) / 1.8) * a.get("fracao", 1.0)
        if q > 0:
            d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * q, fill=rgba(GREEN, p), width=22)
        v = a["valor"]
        d.text((cx, cy - 12), str(conta(v, t, t0 + 0.2, 1.8)) if isinstance(v, int) else v, font=fnt("black", 110 if n < 3 else 90),
               fill=rgba(WHITE, p), anchor="mm")
        d.text((cx, cy + 66), a.get("rotulo", ""), font=fnt("reg", 26), fill=rgba(MUTED, p), anchor="mm")
        tx, qn = el(a.get("nota"))
        d.text((cx, 790), tx or "", font=fnt("reg", 25), fill=rgba(MUTED, prog(t, A(c, qn, t0 + 2), 0.6)), anchor="mm")
    tx, q = el(c.get("selo"))
    pill(d, W / 2, 900, tx, "bold", 32, cor("destaque"), prog(t, A(c, q, c["voz"]) - 0.3, 0.6), cheio=True)


def c_terminal(f, d, c, t):
    cabecalho(d, c, t)
    p = prog(t, 0.4, 0.6)
    box = (140, 280, 1780, 960)
    d.rounded_rectangle(box, radius=18, fill=rgba(cor("fundo_escuro"), 0.88 * p), outline=rgba(WHITE, 0.18 * p), width=2)
    d.rounded_rectangle((box[0], box[1], box[2], box[1] + 48), radius=18, fill=rgba(WHITE, 0.06 * p))
    for i, cc in enumerate((RED, AMBER, GREEN)):
        d.ellipse((170 + i * 30, 296, 186 + i * 30, 312), fill=rgba(cc, p))
    d.text((W / 2, 304), c.get("barra", ""), font=fnt("reg", 20), fill=rgba(MUTED, p), anchor="mm")
    fm, fb = fnt("mono", 26), fnt("monob", 26)
    if c.get("comando") and p > 0:
        d.text((180, 372), "$", font=fb, fill=rgba(cor("destaque"), p), anchor="lm")
        digitando(d, (210, 372), c["comando"], t, 0.8, 1.1, fm, WHITE, p)
    linhas = c["linhas"]
    ta, tb = A(c, c.get("quando_inicio"), 2.0), A(c, c.get("quando_fim"), c["voz"] * 0.9)
    larg = max(d.textlength(l["chamada"], font=fm) for l in linhas)
    xa = 180 + larg + 50
    xs = xa + max(d.textlength(l.get("api", ""), font=fm) for l in linhas) + 50
    xr = xs + 120
    for i, l in enumerate(linhas):
        tk = A(c, l.get("quando"), ta + (tb - ta) * i / max(1, len(linhas) - 1))
        if t < tk:
            continue
        y = 430 + i * 52
        k = int(len(l["chamada"]) * clamp((t - tk) / 0.35))
        d.text((180, y), l["chamada"][:k], font=fm, fill=rgba(WHITE, 1), anchor="lm")
        pk = prog(t, tk + 0.3, 0.4)
        st = str(l.get("status", ""))
        d.text((xa, y), l.get("api", ""), font=fm, fill=rgba(MUTED, pk), anchor="lm")
        d.text((xs, y), st, font=fb, fill=rgba(GREEN if st.startswith("2") else AMBER if st.startswith("5") or st == "0" else RED, pk), anchor="lm")
        d.text((xr, y), l.get("resultado", ""), font=fnt("reg", 26), fill=rgba(WHITE, pk), anchor="lm")
    tx, q = el(c.get("rodape"))
    if tx:
        t0 = A(c, q, c["voz"])
        pf = prog(t, t0, 0.6)
        check(d, 196, 905, 18, (t - t0) / 0.4, GREEN, pf)
        d.text((230, 905), tx, font=fnt("bold", 28), fill=rgba(GREEN, pf), anchor="lm")


def c_antes_agora(f, d, c, t):
    cabecalho(d, c, t)
    rot_a, rot_n = c.get("rotulos", ["ANTES", "AGORA"])
    p = prog(t, 0.6, 0.6)
    d.text((740, 300), rot_a, font=fnt("bold", 24), fill=rgba(MUTED, p), anchor="lm")
    d.text((1290, 300), rot_n, font=fnt("bold", 24), fill=rgba(cor("destaque"), p), anchor="lm")
    itens = c["itens"]
    passo = 180 if len(itens) <= 3 else 150
    for i, it in enumerate(itens):
        tk = A(c, it.get("quando"), 0.8 + i * 3) - 0.2
        p = prog(t, tk, 0.6)
        if p <= 0:
            continue
        y0 = 340 + i * passo
        cy = y0 + (passo - 40) / 2
        dx = (1 - p) * 60
        card(d, (140 + dx, y0, 1780 + dx, y0 + passo - 40), p)
        d.text((180 + dx, cy), it["rotulo"], font=fnt("bold", 32), fill=rgba(WHITE, p), anchor="lm")
        fo = fnt("reg", 30)
        d.text((740 + dx, cy), it["antes"], font=fo, fill=rgba(MUTED, p), anchor="lm")
        ps = ease_io((t - tk - 0.8) / 0.5)
        if ps > 0:
            d.line((736 + dx, cy + 2, 736 + dx + (d.textlength(it["antes"], font=fo) + 8) * ps, cy + 2), fill=rgba(RED, p), width=4)
        seta(d, [(1180 + dx, cy), (1260 + dx, cy)], (t - tk - 1.1) / 0.3, cor("destaque"), p)
        pn = prog(t, tk + 1.3, 0.5)
        d.text((1290 + dx + (1 - pn) * 20, cy), it["agora"], font=fnt("bold", 32), fill=rgba(GREEN, pn), anchor="lm")


def c_linha_tempo(f, d, c, t):
    cabecalho(d, c, t)
    itens = c["itens"]
    n = len(itens)
    xs = [960] if n == 1 else [360 + i * (1200 / (n - 1)) for i in range(n)]
    y = 560
    tempos = [A(c, it.get("quando"), 0.8 + i * 1.5) - 0.15 for i, it in enumerate(itens)]
    d.line((xs[0], y, xs[-1], y), fill=rgba(WHITE, 0.15 * prog(t, tempos[0] - 0.25, 0.5)), width=6)
    for i, it in enumerate(itens):
        tk = tempos[i]
        if i:
            q = ease_io((t - tk + 0.5) / 0.5)
            if q > 0:
                d.line((xs[i - 1], y, xs[i - 1] + (xs[i] - xs[i - 1]) * q, y), fill=cor("destaque"), width=6)
        p = prog(t, tk, 0.5)
        if p <= 0:
            continue
        x = xs[i]
        r = 26 * (0.6 + 0.4 * p)
        atual = it.get("atual")
        if atual:
            pulso = (t * 0.8) % 1
            d.ellipse((x - r - 30 * pulso, y - r - 30 * pulso, x + r + 30 * pulso, y + r + 30 * pulso),
                      outline=rgba(cor("destaque"), (1 - pulso) * p), width=3)
        d.ellipse((x - r, y - r, x + r, y + r), fill=rgba(cor("destaque") if atual else cor("fundo_escuro"), p),
                  outline=rgba(cor("destaque"), p), width=5)
        d.text((x, 470 + (1 - p) * 20), it["titulo"], font=fnt("bold", 36), fill=rgba(WHITE, p), anchor="mm")
        d.text((x, 650), it.get("sub", ""), font=fnt("reg", 26), fill=rgba(MUTED, p), anchor="mm")
        if it.get("tag"):
            pill(d, x, 730, it["tag"], "bold", 22, AMBER, p)
    tx, q = el(c.get("nota"))
    if tx:
        d.text((W / 2, 870), tx, font=fnt("reg", 28), fill=rgba(MUTED, prog(t, A(c, q, c["voz"]), 0.6)), anchor="mm")


def c_encerramento(f, d, c, t):
    linhas = c["linhas"]
    y0 = 520 - (len(linhas) - 1) * 65
    for i, l in enumerate(linhas):
        tx, q = el(l)
        p = prog(t, A(c, q, 0.8 + i * 1.2) - 0.15, 0.6)
        destaque = isinstance(l, dict) and l.get("destaque")
        d.text((W / 2, y0 + i * 130 + (1 - p) * 40), tx, font=fnt("black", 104), fill=rgba(cor("destaque") if destaque else WHITE, p),
               anchor="mm")
    if c.get("rodape"):
        d.text((W / 2, 820), c["rodape"], font=fnt("reg", 28), fill=rgba(MUTED, prog(t, c["voz"] + c["lead"], 0.8)), anchor="mm")


CENA = {"abertura": c_abertura, "manchete": c_manchete, "antes_depois": c_antes_depois, "numeros": c_numeros, "lista": c_lista,
        "grade": c_grade, "aneis": c_aneis, "terminal": c_terminal, "antes_agora": c_antes_agora, "linha_tempo": c_linha_tempo,
        "encerramento": c_encerramento}


class Video:
    def __init__(self, caminho):
        self.pasta = os.path.dirname(os.path.abspath(caminho))
        self.r = rot.carregar(caminho)
        erros = rot.validar(self.r)
        if erros:
            sys.exit("\n".join(erros))
        for k, v in self.r.get("tema", {}).items():
            TEMA[k] = tuple(v)
        FONTES.update(self.r.get("fontes", {}))
        self.cenas = self.r["cenas"]
        self.total = rot.linha_do_tempo(self.r, rot.duracoes_da_pasta(self.r, self.pasta))
        self.limites = [c["ini"] for c in self.cenas[1:]]
        self.capitulos = sum(1 for c in self.cenas if c.get("capitulo"))
        self.fundo = Fundo()

    def cena_em(self, gt):
        for c in self.cenas:
            if gt < c["ini"] + c["dur"]:
                return c
        return self.cenas[-1]

    def quadro(self, gt):
        c = self.cena_em(gt)
        t = gt - c["ini"]
        f = self.fundo.quadro(gt)
        d = Pincel(f)
        CENA[c["tipo"]](f, d, c, t)
        if c.get("capitulo"):
            p = prog(t, 0.3, 0.6)
            d.text((X, H - 46), f"{c['idx']:02d} / {self.capitulos:02d}   {c['capitulo'].upper()}", font=fnt("bold", 20),
                   fill=rgba(MUTED, 0.75 * p), anchor="lm")
            d.text((W - X, H - 46), self.r.get("rodape", "").upper(), font=fnt("bold", 20), fill=rgba(MUTED, 0.5 * p), anchor="rm")
        d.rectangle((0, H - 6, W, H), fill=rgba(WHITE, 0.08))
        d.rectangle((0, H - 6, W * gt / self.total, H), fill=rgba(cor("destaque"), 0.95))
        f.paste(self.fundo.preto, (0, 0), self.fundo.vinheta)
        d = Pincel(f)
        for b in self.limites:  # cortina na cor de destaque, com o nome do próximo capítulo no meio
            u = (gt - b + 0.32) / 0.64
            if 0 <= u <= 1:
                if u < 0.5:
                    x0, x1 = 0, W * ease_io(u / 0.5)
                else:
                    x0, x1 = W * ease_io((u - 0.5) / 0.5), W
                d.rectangle((x0, 0, x1, H), fill=cor("destaque"))
                clara = tuple(min(255, v + 40) for v in cor("destaque"))
                d.rectangle((x1 - 90, 0, x1, H), fill=clara)
                d.rectangle((x1 - 8, 0, x1, H), fill=WHITE)
                prox = self.cena_em(b + 0.01)
                if 0.35 < u < 0.65 and prox.get("capitulo"):
                    d.text((W / 2, H / 2), prox["capitulo"].upper(), font=fnt("black", 120),
                           fill=rgba(cor("fundo_escuro"), 1 - abs(u - 0.5) / 0.15), anchor="mm")
        if gt < 0.8:
            d.rectangle((0, 0, W, H), fill=(0, 0, 0, int(255 * (1 - gt / 0.8))))
        fim = self.total - gt
        if fim < 1.6:
            d.rectangle((0, 0, W, H), fill=(0, 0, 0, int(255 * clamp(1 - fim / 1.6))))
        return f

    # ---------- áudio ----------
    def _ler(self, p):
        with wave.open(p) as w:
            if w.getframerate() != SR or w.getnchannels() != 1:
                sys.exit(f"{p}: esperado WAV mono 44,1 kHz (use voz.py)")
            return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

    def mixar(self, saida):
        N = int((self.total + 0.5) * SR)
        voz = np.zeros(N, np.float32)
        for c in self.cenas:
            v = self._ler(os.path.join(self.pasta, f"voz_{c['id']}.wav"))
            s = int((c["ini"] + c["lead"]) * SR)
            voz[s:s + len(v)] += v[: max(0, N - s)]
        voz *= 0.9 / max(1e-6, np.abs(voz).max())
        musica = self._trilha(N) if self.r.get("trilha", True) else np.zeros(N, np.float32)
        esq, dir_ = self._efeitos(N)
        L, R = voz + musica + esq, voz + musica + dir_
        st = np.stack([L, R], axis=1) * (0.92 / max(np.abs(L).max(), np.abs(R).max()))
        with wave.open(saida, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((st * 32767).astype(np.int16).tobytes())

    def _trilha(self, N):
        hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)  # noqa: E731
        musica = np.zeros(N, np.float32)
        acordes = [[57, 60, 64], [53, 57, 60, 64], [48, 52, 55, 60], [55, 59, 62]]  # Am F C G
        seg, k = 4.0, 0
        while k * seg < self.total + 1:
            s = int(k * seg * SR)
            e = min(N, s + int((seg + 1.6) * SR))
            tt = np.arange(e - s) / SR
            env = np.minimum(1, tt / 1.3) * np.clip((seg + 1.6 - tt) / 1.6, 0, 1)
            ac = acordes[k % 4]
            for m in ac:
                fq = hz(m)
                musica[s:e] += env * (np.sin(2 * np.pi * fq * tt) + 0.35 * np.sin(2 * np.pi * fq * 1.004 * tt + 1)
                                      + 0.10 * np.sin(2 * np.pi * 2 * fq * tt)) * 0.10
            musica[s:e] += env * np.sin(2 * np.pi * hz(ac[0] - 12) * tt) * 0.20
            for j in range(8):
                ps = s + int(j * seg / 8 * SR)
                pe = min(N, ps + int(0.7 * SR))
                if ps >= N:
                    break
                pt = np.arange(pe - ps) / SR
                musica[ps:pe] += np.sin(2 * np.pi * hz(ac[j % len(ac)] + 12) * pt) * np.exp(-pt * 6) * 0.06
            k += 1
        musica /= max(1e-6, np.abs(musica).max())
        voz = np.zeros(N, np.float32)
        for c in self.cenas:
            v = self._ler(os.path.join(self.pasta, f"voz_{c['id']}.wav"))
            s = int((c["ini"] + c["lead"]) * SR)
            voz[s:s + len(v)] += np.abs(v[: max(0, N - s)])
        janela = lambda x, seg: np.convolve(x, np.ones(int(seg * SR), np.float32) / int(seg * SR), mode="same")  # noqa: E731
        atividade = np.clip(janela(voz, 0.3) / 0.03, 0, 1)
        ganho = janela(0.22 - 0.15 * atividade, 0.4)  # trilha abaixa quando há fala
        t = np.arange(N) / SR
        ganho *= np.clip(t / 2.5, 0, 1) * np.clip((self.total - t) / 3.0, 0, 1)
        return (musica * ganho).astype(np.float32)

    def _efeitos(self, N):
        rng = np.random.default_rng(3)
        esq, dir_ = np.zeros(N, np.float32), np.zeros(N, np.float32)
        for b in self.limites:  # whoosh com pan da esquerda para a direita, junto da cortina
            n, s = int(0.7 * SR), int((b - 0.42) * SR)
            ruido = rng.standard_normal(n)
            x = np.linspace(0, 1, n)
            alfa = 0.02 + 0.35 * np.sin(np.pi * x) ** 2
            out = np.zeros(n)
            y = 0.0
            for i in range(n):
                y += alfa[i] * (ruido[i] - y)
                out[i] = y
            out *= np.sin(np.pi * x) ** 2 * 0.55
            esq[s:s + n] += (out * (1 - x)).astype(np.float32)
            dir_[s:s + n] += (out * x).astype(np.float32)
        n, s = int(1.6 * SR), int(max(0.0, self.cenas[0]["lead"] - 0.85) * SR)  # impacto grave na abertura
        tt = np.arange(n) / SR
        boom = (np.sin(2 * np.pi * 52 * tt) * np.exp(-tt * 3.0) * 0.6).astype(np.float32)
        esq[s:s + n] += boom
        dir_[s:s + n] += boom
        return esq, dir_

    def video(self, saida):
        audio = os.path.join(self.pasta, "_mix.wav")
        self.mixar(audio)
        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", saida]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        n = int(self.total * FPS)
        for i in range(n):
            pr.stdin.write(self.quadro(i / FPS).tobytes())
            if i % 600 == 0:
                print(f"{i}/{n}", flush=True)
        pr.stdin.close()
        pr.wait()
        os.remove(audio)
        if pr.returncode:
            sys.exit(f"ffmpeg saiu com {pr.returncode}")
        print(f"ok {saida} ({self.total:.1f}s)")

    def folha(self, saida):
        ims = [self.quadro(c["ini"] + c["dur"] - 1.0).resize((640, 360)) for c in self.cenas]
        cols = 3
        sh = Image.new("RGB", (640 * cols, 360 * math.ceil(len(ims) / cols)))
        for i, im in enumerate(ims):
            sh.paste(im, ((i % cols) * 640, (i // cols) * 360))
        sh.save(saida)
        print(f"ok {saida}")


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[1] not in ("folha", "previa", "video"):
        sys.exit(__doc__)
    v = Video(a[0])
    if a[1] == "folha":
        v.folha(a[2] if len(a) > 2 else os.path.join(v.pasta, "folha.png"))
    elif a[1] == "previa":
        for s in a[2:]:
            v.quadro(float(s)).save(os.path.join(v.pasta, f"previa_{float(s):06.1f}.png"))
        print(f"total {v.total:.1f}s")
    else:
        v.video(a[2])


if __name__ == "__main__":
    main()
