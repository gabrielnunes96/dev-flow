"""Roteiro do vídeo-resumo: leitura, validação e linha do tempo. Só biblioteca padrão.

Uso: python -I roteiro.py validar <roteiro.json>
     python -I roteiro.py tempos <roteiro.json>      (exige os voz_<id>.wav na pasta do roteiro)
"""
import json
import os
import re
import sys
import wave

# tipo de cena -> campos obrigatórios
TIPOS = {
    "abertura": ["titulo"],
    "manchete": ["titulo"],
    "antes_depois": ["titulo", "antes", "agora"],
    "numeros": ["titulo", "cartoes"],
    "lista": ["titulo", "itens"],
    "grade": ["titulo", "itens"],
    "aneis": ["titulo", "aneis"],
    "terminal": ["titulo", "linhas"],
    "antes_agora": ["titulo", "itens"],
    "linha_tempo": ["titulo", "itens"],
    "encerramento": ["linhas"],
}
# "tipo.campo" -> máximo de itens que cabem na tela
LIMITES = {
    "numeros.cartoes": 3, "lista.itens": 5, "grade.itens": 12, "aneis.aneis": 3, "terminal.linhas": 10,
    "antes_agora.itens": 4, "linha_tempo.itens": 5, "encerramento.linhas": 4,
}
LEAD, TAIL = 0.7, 0.9  # respiro antes e depois da fala de cada cena (s)


def carregar(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def chave(q):
    """'palavra' | ['palavra', deslocamento] | número (segundos absolutos na cena) -> (palavra|None, deslocamento)."""
    if isinstance(q, (int, float)):
        return None, float(q)
    if isinstance(q, list):
        return q[0], float(q[1])
    return q, 0.0


def quandos(no):
    """Todos os valores de 'quando' (e 'quando_*') dentro de uma cena."""
    if isinstance(no, dict):
        for k, v in no.items():
            if k == "quando" or k.startswith("quando_"):
                yield v
            else:
                yield from quandos(v)
    elif isinstance(no, list):
        for v in no:
            yield from quandos(v)


def validar(r):
    erros = []
    cenas = r.get("cenas")
    if not isinstance(cenas, list) or not cenas:
        return ["roteiro sem 'cenas'"]
    vistos = set()
    for i, c in enumerate(cenas):
        nome = c.get("id", f"#{i}")
        if not re.fullmatch(r"[a-z0-9_]+", str(c.get("id", ""))):
            erros.append(f"{nome}: id deve ser minúsculo, com letras, números e _")
        if nome in vistos:
            erros.append(f"{nome}: id repetido")
        vistos.add(nome)
        tipo = c.get("tipo")
        if tipo not in TIPOS:
            erros.append(f"{nome}: tipo desconhecido '{tipo}' (use {', '.join(TIPOS)})")
            continue
        if not str(c.get("fala", "")).strip():
            erros.append(f"{nome}: fala vazia")
        for campo in TIPOS[tipo]:
            if campo not in c:
                erros.append(f"{nome}: falta '{campo}'")
        for alvo, maximo in LIMITES.items():
            t, campo = alvo.split(".")
            if t == tipo and len(c.get(campo, [])) > maximo:
                erros.append(f"{nome}: '{campo}' tem {len(c[campo])} itens (máximo {maximo})")
        if tipo == "antes_depois":
            for lado in ("antes", "agora"):
                camadas = c.get(lado, {}).get("camadas", [])
                if not 1 <= len(camadas) <= 3 or any(not 1 <= len(cam) <= 3 for cam in camadas):
                    erros.append(f"{nome}: '{lado}.camadas' precisa de 1 a 3 camadas com 1 a 3 caixas")
        fala = c.get("fala", "")
        for q in quandos(c):
            kw, _ = chave(q)
            if kw is not None and kw not in fala:
                erros.append(f"{nome}: quando '{kw}' não aparece na fala")
    return erros


def duracao_wav(caminho):
    with wave.open(caminho) as w:
        return w.getnframes() / w.getframerate()


def linha_do_tempo(r, duracoes):
    """Preenche ini/dur/lead/voz/idx de cada cena a partir da duração das falas; devolve a duração total."""
    t = 0.0
    for i, c in enumerate(r["cenas"]):
        c["voz"] = duracoes[c["id"]]
        c["lead"] = LEAD + (0.6 if c["tipo"] == "abertura" else 0)
        c["dur"] = c["lead"] + c["voz"] + TAIL + (2.2 if c["tipo"] == "encerramento" else 0)
        c["ini"], c["idx"] = t, i
        t += c["dur"]
    return t


def at(c, q, padrao=0.0):
    """Instante (s, relativo à cena) de um 'quando': proporcional à posição da palavra na fala."""
    if q is None:
        return padrao
    kw, off = chave(q)
    if kw is None:
        return off
    return c["lead"] + c["voz"] * c["fala"].find(kw) / len(c["fala"]) + off


def duracoes_da_pasta(r, pasta):
    return {c["id"]: duracao_wav(os.path.join(pasta, f"voz_{c['id']}.wav")) for c in r["cenas"]}


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("validar", "tempos"):
        sys.exit(__doc__)
    r = carregar(sys.argv[2])
    erros = validar(r)
    if erros:
        print("\n".join(erros))
        sys.exit(1)
    if sys.argv[1] == "validar":
        print(f"ok: {len(r['cenas'])} cenas")
        return
    total = linha_do_tempo(r, duracoes_da_pasta(r, os.path.dirname(os.path.abspath(sys.argv[2]))))
    for c in r["cenas"]:
        print(f"{c['ini']:7.1f}s  {c['id']}  ({c['dur']:.1f}s)")
    print(f"total {total:.1f}s")


if __name__ == "__main__":
    main()
