"""Análises já feitas, neste computador. Só biblioteca padrão.

A chave é o hash do conteúdo. O mesmo arquivo, com os mesmos bytes, reabre
sem ler de novo. DEVFLOW_LOGS_CACHE troca a pasta. Vazio desliga.
"""
import hashlib
import json
import os
import re
import time

VERSAO = 1
MAX_ITENS = 30


def diretorio(raiz=None):
    if raiz is not None:
        return raiz
    env = os.environ.get("DEVFLOW_LOGS_CACHE")
    if env == "":
        return None
    if env:
        return env
    return os.path.join(os.path.expanduser("~"), ".cache", "dev-flow", "logs")


def chave_valida(chave):
    return bool(re.fullmatch(r"[0-9a-f]{64}", chave or ""))


def chave_de_bytes(pares):
    h = hashlib.sha256()
    h.update(f"dev-flow-logs:{VERSAO}\n".encode())
    for nome, dados in pares:
        blob = nome.encode("utf-8", "replace")
        h.update(blob)
        h.update(b"\0")
        h.update(str(len(dados)).encode())
        h.update(b"\0")
        h.update(dados)
        h.update(b"\0")
    return h.hexdigest()


def _ler_arquivo(caminho):
    with open(caminho, "rb") as f:
        return f.read()


def chave_de_caminhos(caminhos):
    pares = []
    for caminho in caminhos:
        if os.path.isdir(caminho):
            for raiz, dirs, nomes in os.walk(caminho):
                dirs.sort()
                for nome in sorted(nomes):
                    cheio = os.path.join(raiz, nome)
                    if os.path.islink(cheio) or not os.path.isfile(cheio):
                        continue
                    rel = os.path.relpath(cheio, caminho).replace("\\", "/")
                    pares.append((rel, _ler_arquivo(cheio)))
        else:
            pares.append((os.path.basename(caminho), _ler_arquivo(caminho)))
    return chave_de_bytes(pares)


def _caminho(chave, raiz=None):
    base = diretorio(raiz)
    if not base or not chave_valida(chave):
        return None
    return os.path.join(base, chave + ".json")


def ler(chave, raiz=None):
    caminho = _caminho(chave, raiz)
    if not caminho or not os.path.isfile(caminho):
        return None
    try:
        with open(caminho, encoding="utf-8") as f:
            dado = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(dado, dict) or dado.get("versao") != VERSAO:
        return None
    relatorio = dado.get("relatorio")
    if not isinstance(relatorio, dict):
        return None
    return relatorio


def _indice_caminho(base):
    return os.path.join(base, "indice.json")


def _ler_indice(base):
    caminho = _indice_caminho(base)
    if not os.path.isfile(caminho):
        return []
    try:
        with open(caminho, encoding="utf-8") as f:
            dado = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(dado, list):
        return []
    return [item for item in dado if isinstance(item, dict) and chave_valida(item.get("chave"))]


def listar(raiz=None):
    base = diretorio(raiz)
    if not base:
        return []
    return _ler_indice(base)


def guardar(chave, relatorio, nomes, raiz=None):
    base = diretorio(raiz)
    if not base or not chave_valida(chave):
        return
    os.makedirs(base, exist_ok=True)
    quando = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    payload = {"versao": VERSAO, "quando": quando, "nomes": list(nomes), "relatorio": relatorio}
    dest = os.path.join(base, chave + ".json")
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(tmp, dest)
    item = {
        "chave": chave,
        "quando": quando,
        "nomes": list(nomes),
        "resumo": relatorio.get("resumo") or {},
    }
    indice = [item] + [i for i in _ler_indice(base) if i.get("chave") != chave]
    indice = indice[:MAX_ITENS]
    ind = _indice_caminho(base)
    tmp = ind + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False)
    os.replace(tmp, ind)
