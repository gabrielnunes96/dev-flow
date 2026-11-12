"""Analisa um conjunto de logs e separa erro e aviso.

Uso:
  python -I analisar.py <entrada>... [--saida DIR] [--estrito]

Entrada, num comando só: um arquivo, uma pasta, .gz, .zip, .tar, .tar.gz, .tgz ou .tar.bz2.
Um zip ou tar traz um log ou vários. Vários zips, tars e arquivos soltos juntos
saem num único relatório.
Sem --saida, grava ./analise-logs/relatorio.json, painel.html e achados.xlsx.
Código 0: análise concluída. 1: entrada inválida. 2: --estrito com erro.
"""
import gzip
import html
import json
import math
import os
import re
import sys
import tarfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guarda  # noqa: E402
import planilha  # noqa: E402

MAX_ARQUIVO = 20 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MAX_ARQUIVOS = 20000
MAX_AMOSTRA = 3
MAX_TEXTO = 500

CAMINHOS_RUIDO = {
    "/favicon.ico",
    "/robots.txt",
    "/apple-touch-icon.png",
    "/apple-touch-icon-precomposed.png",
}
RUIDO_CONEXAO = (
    "broken pipe",
    "connection reset by peer",
    "client closed connection",
    "an existing connection was forcibly closed",
    "connection aborted",
)
NIVEL_BAIXO = {"info", "debug", "warn", "warning", "trace"}
NIVEL_ALTO = {"error", "fatal", "critical", "panic"}

RE_NIVEL = re.compile(
    r"\b(FATAL|CRITICAL|ERROR|PANIC|WARN(?:ING)?|INFO|DEBUG|TRACE|ERRO|AVISO)\b", re.I)
RE_STATUS = re.compile(
    r"\b(?:status(?:_?code)?|http_status|statusCode)\s*[=:]\s*(\d{3})\b", re.I)
RE_UPSTREAM = re.compile(r"\bupstream_status\s*[=:]\s*(\d{3})\b", re.I)
RE_HTTP = re.compile(r"HTTP/\d(?:\.\d)?\s+(\d{3})\b")
RE_METODO = re.compile(
    r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(\S+)\s+(\d{3})\b", re.I)
RE_CAMINHO = re.compile(r"\b(?:path|url|uri)\s*[=:]\s*(\S+)", re.I)
RE_CAMINHO_JSON = re.compile(r'"(?:path|url|uri)"\s*:\s*"([^"]+)"', re.I)
RE_QUANDO = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
RE_EXC = re.compile(
    r"(?i:traceback \(most recent call last\)"
    r"|exception in thread"
    r"|\bpanic:"
    r"|\bCaused by:)"
    r"|\b[A-Za-z_][A-Za-z0-9_.]*Exception\b"
    r"|\b[A-Za-z_][A-Za-z0-9_]*Error\b"
)
RE_TIPO = re.compile(r"\b([A-Za-z_][A-Za-z0-9_.]*(?:Exception|Error))\b")
RE_SUCESSO_FALSO = re.compile(
    r'"(?:success|ok)"\s*:\s*false|\b(?:success|ok)\s*[=:]\s*false\b', re.I)
RE_ERRO_VAZIO = re.compile(
    r'"(?:errors?)"\s*:\s*(?:null|""|\[\s*\])'
    r"|\b(?:error_count|errorCount|errors|falhas)\s*[=:]\s*0\b",
    re.I)
RE_TIMEOUT = re.compile(
    r"\b(?:timed out|timeout exceeded|deadline exceeded|i/o timeout)\b", re.I)
RE_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
RE_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
RE_HEX = re.compile(r"\b[0-9a-f]{16,}\b", re.I)
RE_NUM = re.compile(r"\d+")


class EntradaInvalida(Exception):
    pass


def _caminho(bruto):
    if not bruto:
        return None
    bruto = bruto.strip().strip('"').strip("'")
    bruto = bruto.split("?", 1)[0].split("#", 1)[0]
    if "://" in bruto:
        bruto = bruto.split("://", 1)[1]
        bruto = bruto.split("/", 1)[1] if "/" in bruto else ""
        bruto = "/" + bruto
    if not bruto.startswith("/"):
        bruto = "/" + bruto
    return bruto or "/"


def _nivel(texto):
    m = RE_NIVEL.search(texto)
    if not m:
        return None
    return _canon_nivel(m.group(1))


def _canon_nivel(nivel):
    n = nivel.lower()
    if n in ("warning", "aviso"):
        return "warn"
    if n == "erro":
        return "error"
    return n


def _familia(nivel):
    if nivel in ("error", "fatal", "critical", "panic"):
        return "error"
    if nivel in ("warn", "warning"):
        return "warning"
    if nivel == "info":
        return "info"
    if nivel in ("debug", "trace"):
        return "debug"
    return "outro"


def _inteiro(valor):
    if isinstance(valor, bool) or valor is None:
        return None
    if isinstance(valor, int) and 100 <= valor <= 599:
        return valor
    if isinstance(valor, str) and re.fullmatch(r"\d{3}", valor):
        return int(valor)
    return None


def _do_json(texto):
    s = texto.strip()
    if not s.startswith("{"):
        return {}
    try:
        dado = json.loads(s)
    except json.JSONDecodeError:
        return {}
    if not isinstance(dado, dict):
        return {}
    nivel = dado.get("level") or dado.get("severity") or dado.get("lvl")
    if isinstance(nivel, str):
        nivel = _canon_nivel(nivel)
    else:
        nivel = None
    err = dado.get("error")
    msg = dado.get("message") or dado.get("msg") or (err if isinstance(err, str) else None)
    status = _inteiro(dado.get("status") or dado.get("statusCode") or dado.get("status_code"))
    upstream = _inteiro(dado.get("upstream_status") or dado.get("upstreamStatus"))
    caminho = dado.get("path") or dado.get("url") or dado.get("uri")
    if not isinstance(caminho, str):
        caminho = None
    return {
        "nivel": nivel,
        "mensagem": msg if isinstance(msg, str) else None,
        "status": status,
        "upstream": upstream,
        "caminho": _caminho(caminho) if caminho else None,
        "erro_campo": isinstance(err, str) and bool(err.strip()),
    }


def _sinais(texto, extra):
    nivel = extra.get("nivel") or _nivel(texto)
    status = extra.get("status")
    upstream = extra.get("upstream")
    caminho = extra.get("caminho")
    if status is None:
        m = RE_UPSTREAM.search(texto)
        if m:
            upstream = upstream or int(m.group(1))
        m = RE_STATUS.search(texto)
        if m and m.group(0).lower().startswith("upstream"):
            upstream = upstream or int(m.group(1))
        elif m:
            status = int(m.group(1))
        m = RE_HTTP.search(texto)
        if m and status is None:
            status = int(m.group(1))
        m = RE_METODO.search(texto)
        if m:
            caminho = caminho or _caminho(m.group(1))
            if status is None:
                status = int(m.group(2))
    if caminho is None:
        m = RE_CAMINHO_JSON.search(texto) or RE_CAMINHO.search(texto)
        if m:
            caminho = _caminho(m.group(1))
    corpo = texto
    if nivel:
        corpo = re.sub(r"\b" + re.escape(nivel) + r"\b", " ", corpo, count=1, flags=re.I)
    tipo = None
    tm = RE_TIPO.search(corpo)
    if tm:
        tipo = tm.group(1)
    return {
        "nivel": nivel,
        "status": status,
        "upstream": upstream,
        "caminho": caminho,
        "excecao": bool(RE_EXC.search(corpo)),
        "tipo": tipo,
        "sucesso_falso": bool(RE_SUCESSO_FALSO.search(texto)),
        "erro_campo": bool(extra.get("erro_campo")),
        "erro_vazio": bool(RE_ERRO_VAZIO.search(texto)),
        "timeout": bool(RE_TIMEOUT.search(texto)),
        "conexao": any(p in texto.lower() for p in RUIDO_CONEXAO),
    }


def _continuacao(linha):
    if linha.startswith((" ", "\t")):
        return True
    s = linha.lstrip()
    return s.startswith(("at ", "Caused by:", 'File "', "...", "^", "--- End of", "---"))


def _blocos(linhas):
    i, n = 0, len(linhas)
    while i < n:
        inicio = i
        i += 1
        if RE_EXC.search(linhas[inicio]):
            while i < n and _continuacao(linhas[i]):
                i += 1
        yield inicio + 1, "\n".join(linhas[inicio:i])


def classificar(texto):
    """Devolve (achado ou None, retornos, família do nível). achado não inclui amostras."""
    extra = _do_json(texto)
    s = _sinais(texto, extra)
    retornos = []
    if s["status"] is not None:
        retornos.append({"codigo": s["status"], "como": "status"})
    if s["upstream"] is not None:
        retornos.append({"codigo": s["upstream"], "como": "upstream"})
    status, upstream, nivel = s["status"], s["upstream"], s["nivel"]
    familia = _familia(nivel)

    def sair(achado):
        if achado is not None:
            achado["nivel"] = familia
        return achado, retornos, familia

    falha_grave = (status is not None and status >= 500) or (upstream is not None and upstream >= 500)
    ruido_caminho = s["caminho"] in CAMINHOS_RUIDO and not falha_grave
    if ruido_caminho or (s["conexao"] and not falha_grave):
        return sair(None)
    if s["erro_vazio"] and not s["excecao"] and not s["sucesso_falso"] and not falha_grave and not s["timeout"]:
        return sair(None)
    if s["sucesso_falso"] and (status is None or status < 400):
        return sair(_achado("erro", "HTTP 2xx com falha no corpo" if status else "corpo diz success=false",
                            "success=false", status))
    if s["erro_campo"] and (nivel in NIVEL_BAIXO or nivel is None) and (status is None or status < 400):
        return sair(_achado("erro", "campo error em nível baixo", "campo error", status))
    if upstream is not None and upstream >= 500 and (status is None or status < 400):
        return sair(_achado("erro", f"HTTP {status or '2xx'} com upstream {upstream}",
                            f"upstream {upstream}", status))
    if status is not None and status >= 500 and nivel in NIVEL_BAIXO:
        return sair(_achado("erro", f"nível {nivel} esconde HTTP {status}", f"HTTP {status}", status))
    if s["excecao"] and nivel in NIVEL_BAIXO:
        return sair(_achado("erro", f"exceção em nível {nivel}", s["tipo"] or "exceção", status))
    if s["timeout"] and (nivel in NIVEL_BAIXO or nivel is None) and not falha_grave:
        return sair(_achado("erro", "timeout fora do nível error", "timeout", status))
    if status is not None and status >= 500:
        return sair(_achado("erro", f"HTTP {status}", s["tipo"] or f"HTTP {status}", status))
    if nivel in NIVEL_ALTO or (s["excecao"] and nivel not in NIVEL_BAIXO):
        return sair(_achado("erro", "nível " + (nivel or "error"), _titulo_util(texto, s["tipo"]), status))
    if status is not None and 400 <= status < 500:
        return sair(_achado("aviso", f"HTTP {status}", s["caminho"] or f"HTTP {status}", status))
    return sair(None)


def _achado(classe, motivo, titulo, retorno):
    return {"classe": classe, "motivo": motivo, "titulo": titulo[:140], "retorno": retorno}


def _titulo_util(texto, tipo):
    if tipo and tipo.lower() not in ("error", "erro"):
        return tipo
    linha = texto.splitlines()[0].strip()
    linha = re.sub(r"^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s*-\s*", "", linha)
    linha = re.sub(
        r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\s*",
        "",
        linha,
    )
    return linha or tipo or "erro"


def normalizar(texto):
    t = texto.splitlines()[0].lower()
    t = RE_UUID.sub("<uuid>", t)
    t = RE_IP.sub("<ip>", t)
    t = RE_HEX.sub("<hex>", t)
    t = RE_NUM.sub("<n>", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:180]


def montar(documentos):
    """documentos: {nome, texto} ou {nome, ignorado}. Devolve o relatório."""
    arquivos = []
    grupos = {}
    retornos = {}
    ordem = []
    niveis = {"error": 0, "warning": 0, "info": 0, "debug": 0, "outro": 0}
    for doc in documentos:
        if doc.get("ignorado"):
            arquivos.append({"nome": doc["nome"], "bytes": doc.get("bytes", 0), "linhas": 0, "ignorado": doc["ignorado"]})
            continue
        texto = doc.get("texto") or ""
        linhas = texto.splitlines()
        arquivos.append({"nome": doc["nome"], "bytes": doc.get("bytes", len(texto.encode("utf-8"))), "linhas": len(linhas), "ignorado": None})
        for numero, bloco in _blocos(linhas):
            achado, cods, familia = classificar(bloco)
            niveis[familia] += 1
            for c in cods:
                chave = (c["codigo"], c["como"])
                retornos[chave] = retornos.get(chave, 0) + 1
            if not achado:
                continue
            chave = (achado["classe"], achado["motivo"], achado["retorno"], normalizar(bloco))
            if chave not in grupos:
                grupos[chave] = {
                    "classe": achado["classe"],
                    "motivo": achado["motivo"],
                    "titulo": achado["titulo"],
                    "retorno": achado["retorno"],
                    "nivel": achado.get("nivel") or "outro",
                    "contagem": 0,
                    "arquivos": [],
                    "amostras": [],
                }
                ordem.append(chave)
            g = grupos[chave]
            g["contagem"] += 1
            if doc["nome"] not in g["arquivos"]:
                g["arquivos"].append(doc["nome"])
            if len(g["amostras"]) < MAX_AMOSTRA:
                quando = RE_QUANDO.search(bloco)
                g["amostras"].append({
                    "arquivo": doc["nome"],
                    "linha": numero,
                    "quando": quando.group(0) if quando else None,
                    "texto": _cortar_amostra(bloco),
                })
    rank = {"erro": 0, "aviso": 1}
    chaves = sorted(ordem, key=lambda k: (rank[k[0]], -grupos[k]["contagem"], k[1]))
    achados = []
    for i, k in enumerate(chaves, 1):
        item = grupos[k]
        item["id"] = f"A{i}"
        achados.append(item)
    contagem = {c: sum(a["contagem"] for a in achados if a["classe"] == c)
                for c in ("erro", "aviso")}
    return {
        "resumo": {
            "arquivos": len(arquivos),
            "linhas": sum(a["linhas"] for a in arquivos),
            "erros": contagem["erro"],
            "avisos": contagem["aviso"],
            "niveis": niveis,
        },
        "arquivos": arquivos,
        "achados": achados,
        "retornos": [
            {"codigo": cod, "como": como, "contagem": n}
            for (cod, como), n in sorted(retornos.items())
        ],
    }


def _decodificar(data, nome):
    if len(data) > MAX_ARQUIVO:
        return {"nome": nome, "bytes": len(data), "ignorado": "arquivo grande demais"}
    amostra = data[:4096]
    if amostra and all(b == 0 for b in amostra):
        return {"nome": nome, "bytes": len(data), "ignorado": "vazio"}
    if b"\x00" in amostra:
        return {"nome": nome, "bytes": len(data), "ignorado": "binário"}
    try:
        texto = data.decode("utf-8")
    except UnicodeDecodeError:
        texto = data.decode("latin-1")
    return {"nome": nome, "bytes": len(data), "texto": texto}


def _ruido(nome):
    partes = nome.replace("\\", "/").split("/")
    if any(p == "__MACOSX" for p in partes):
        return True
    base = partes[-1] if partes else ""
    return base.startswith("._") or base == ".DS_Store"


def _nome_seguro(nome):
    partes = nome.replace("\\", "/").split("/")
    if nome.startswith("/") or any(p == ".." for p in partes):
        raise EntradaInvalida(f"caminho inseguro no arquivo: {nome}")
    return "/".join(p for p in partes if p not in ("", "."))


def _ler_arquivo(caminho, nome):
    tamanho = os.path.getsize(caminho)
    if tamanho > MAX_ARQUIVO:
        return {"nome": nome, "bytes": tamanho, "ignorado": "arquivo grande demais"}
    with open(caminho, "rb") as f:
        data = f.read()
    return _decodificar(data, nome)


def _entrar_zip(caminho):
    docs = []
    total = 0
    with zipfile.ZipFile(caminho) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            nome = _nome_seguro(info.filename)
            if _ruido(nome):
                continue
            if info.file_size > MAX_ARQUIVO:
                docs.append({"nome": nome, "bytes": info.file_size, "ignorado": "arquivo grande demais"})
                continue
            total += info.file_size
            if total > MAX_TOTAL or len(docs) >= MAX_ARQUIVOS:
                raise EntradaInvalida("conjunto grande demais")
            docs.append(_decodificar(z.read(info), nome))
    return docs


def _entrar_tar(caminho):
    docs = []
    total = 0
    with tarfile.open(caminho, "r:*") as t:
        for membro in t.getmembers():
            if not membro.isfile() or membro.issym() or membro.islnk():
                continue
            nome = _nome_seguro(membro.name)
            if _ruido(nome):
                continue
            if membro.size > MAX_ARQUIVO:
                docs.append({"nome": nome, "bytes": membro.size, "ignorado": "arquivo grande demais"})
                continue
            total += membro.size
            if total > MAX_TOTAL or len(docs) >= MAX_ARQUIVOS:
                raise EntradaInvalida("conjunto grande demais")
            extraido = t.extractfile(membro)
            data = extraido.read() if extraido is not None else b""
            docs.append(_decodificar(data, nome))
    return docs


def _ler_caminho(cheio, nome):
    baixo = nome.lower()
    if baixo.endswith(".zip"):
        return _entrar_zip(cheio)
    if baixo.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2")):
        return _entrar_tar(cheio)
    if baixo.endswith(".gz"):
        with gzip.open(cheio, "rb") as f:
            data = f.read(MAX_ARQUIVO + 1)
        return [_decodificar(data, nome)]
    return [_ler_arquivo(cheio, nome)]


def coletar(caminhos):
    docs = []

    def acrescentar(novos):
        docs.extend(novos)
        if len(docs) > MAX_ARQUIVOS:
            raise EntradaInvalida("conjunto grande demais")

    for caminho in caminhos:
        if not os.path.exists(caminho):
            raise EntradaInvalida(f"não encontrado: {caminho}")
        if os.path.isdir(caminho):
            achou = False
            for raiz, dirs, nomes in os.walk(caminho):
                dirs.sort()
                for nome in sorted(nomes):
                    cheio = os.path.join(raiz, nome)
                    if os.path.islink(cheio):
                        continue
                    rel = os.path.relpath(cheio, caminho).replace("\\", "/")
                    if _ruido(rel):
                        continue
                    achou = True
                    acrescentar(_ler_caminho(cheio, rel))
            if not achou:
                raise EntradaInvalida("nenhum arquivo de log")
            continue
        acrescentar(_ler_caminho(caminho, os.path.basename(caminho)))
    if not docs:
        raise EntradaInvalida("nenhum arquivo de log")
    return docs


def analisar_entradas(caminhos):
    return montar(coletar(caminhos))


ESTILO = """
:root {
  --matiz: 230; --croma-acento: 0.14; --croma-neutro: 0.012;
  --n-0: oklch(99.5% calc(var(--croma-neutro) * 0.5) var(--matiz));
  --n-50: oklch(98% var(--croma-neutro) var(--matiz));
  --n-100: oklch(96% var(--croma-neutro) var(--matiz));
  --n-200: oklch(92% var(--croma-neutro) var(--matiz));
  --n-400: oklch(75% var(--croma-neutro) var(--matiz));
  --n-500: oklch(60% var(--croma-neutro) var(--matiz));
  --n-600: oklch(47% var(--croma-neutro) var(--matiz));
  --n-800: oklch(27% var(--croma-neutro) var(--matiz));
  --n-900: oklch(21% var(--croma-neutro) var(--matiz));
  --n-950: oklch(16% var(--croma-neutro) var(--matiz));
  --n-1000: oklch(13% var(--croma-neutro) var(--matiz));
  --a-100: oklch(95% calc(var(--croma-acento) * 0.25) var(--matiz));
  --a-500: oklch(62% var(--croma-acento) var(--matiz));
  --a-600: oklch(54% var(--croma-acento) var(--matiz));
  --a-700: oklch(47% var(--croma-acento) var(--matiz));
  --cor-fundo: var(--n-50); --cor-superficie: var(--n-0); --cor-sutil: var(--n-100);
  --cor-borda: var(--n-200); --cor-borda-forte: var(--n-500);
  --cor-texto: var(--n-900); --cor-texto-suave: var(--n-600);
  --cor-acento: var(--a-600); --cor-acento-hover: var(--a-700);
  --cor-acento-suave: var(--a-100); --cor-sobre-acento: oklch(100% 0 0); --cor-foco: var(--a-500);
  --cor-perigo: oklch(55% 0.2 27); --cor-perigo-suave: oklch(96% 0.03 27);
  --cor-aviso: oklch(54% 0.13 70); --cor-aviso-suave: oklch(97% 0.04 85);
  --fonte-texto: "Segoe UI", system-ui, -apple-system, sans-serif;
  --fonte-mono: ui-monospace, "SF Mono", Consolas, monospace;
  --texto-sm: 0.875rem; --texto-md: 1rem; --texto-lg: 1.25rem; --texto-xl: 1.5625rem; --texto-2xl: 1.9375rem;
  --altura-texto: 1.5; --altura-titulo: 1.2; --peso-normal: 400; --peso-medio: 550; --peso-forte: 650;
  --espaco-1: 4px; --espaco-2: 8px; --espaco-3: 12px; --espaco-4: 16px; --espaco-5: 24px; --espaco-6: 32px; --espaco-7: 48px; --espaco-8: 64px;
  --raio-p: 6px; --raio-m: 10px; --raio-g: 16px;
  --sombra-1: 0 1px 2px oklch(20% 0.02 var(--matiz) / 0.06), 0 1px 3px oklch(20% 0.02 var(--matiz) / 0.08);
  --anel-foco: 0 0 0 2px var(--cor-fundo), 0 0 0 4px var(--cor-foco);
  --dur-rapida: 120ms; --dur-media: 220ms;
  --curva-entrada: cubic-bezier(0.16, 1, 0.3, 1); --curva-padrao: cubic-bezier(0.65, 0, 0.35, 1);
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root {
    --cor-fundo: var(--n-1000); --cor-superficie: var(--n-950); --cor-sutil: var(--n-900);
    --cor-borda: var(--n-800); --cor-borda-forte: oklch(52% var(--croma-neutro) var(--matiz));
    --cor-texto: oklch(94% var(--croma-neutro) var(--matiz)); --cor-texto-suave: var(--n-400);
    --cor-acento: oklch(72% calc(var(--croma-acento) * 0.85) var(--matiz));
    --cor-acento-hover: oklch(78% calc(var(--croma-acento) * 0.8) var(--matiz));
    --cor-acento-suave: oklch(28% calc(var(--croma-acento) * 0.4) var(--matiz));
    --cor-sobre-acento: var(--n-1000); --cor-foco: oklch(75% var(--croma-acento) var(--matiz));
    --cor-perigo: oklch(70% 0.17 27); --cor-perigo-suave: oklch(27% 0.06 27);
    --cor-aviso: oklch(78% 0.14 75); --cor-aviso-suave: oklch(28% 0.05 75);
    color-scheme: dark;
  }
}
body { margin: 0; background: var(--cor-fundo); color: var(--cor-texto);
  font: var(--peso-normal) var(--texto-md)/var(--altura-texto) var(--fonte-texto); }
.miolo { max-width: 920px; margin: 0 auto; padding: var(--espaco-6) var(--espaco-5) var(--espaco-8); }
.marca { margin: 0 0 var(--espaco-2); color: var(--cor-texto-suave); font-size: var(--texto-sm); letter-spacing: 0.06em; text-transform: uppercase; }
h1, h2, h3 { font-weight: var(--peso-forte); line-height: var(--altura-titulo); letter-spacing: -0.02em; }
h1 { margin: 0; font-size: var(--texto-2xl); }
h2 { margin: var(--espaco-6) 0 var(--espaco-3); font-size: var(--texto-lg); }
.lead, .resumo { margin: var(--espaco-3) 0 0; max-width: 66ch; color: var(--cor-texto-suave); }
.veredito { margin: var(--espaco-4) 0 0; max-width: 34em; font-size: var(--texto-lg); font-weight: var(--peso-medio); letter-spacing: -0.015em; }
details.arquivos, details.mais { margin-top: var(--espaco-3); }
summary { cursor: pointer; color: var(--cor-acento); }
.achado-principal h3 { font-size: var(--texto-lg); }
.voltar { margin: 0 0 var(--espaco-5); }
a { color: var(--cor-acento); }
a:hover { color: var(--cor-acento-hover); }
:focus-visible { outline: none; box-shadow: var(--anel-foco); border-radius: var(--raio-p); }
.zona { position: relative; display: grid; gap: var(--espaco-1); margin-top: var(--espaco-6);
  padding: var(--espaco-7) var(--espaco-5); border: 1px dashed var(--cor-borda-forte); border-radius: var(--raio-g);
  background: var(--cor-superficie); text-align: center; cursor: pointer;
  transition: border-color var(--dur-rapida) var(--curva-padrao), background var(--dur-rapida) var(--curva-padrao); }
.zona:hover, .zona.sobre { border-color: var(--cor-acento); background: var(--cor-acento-suave); }
.zona:focus-within { box-shadow: var(--anel-foco); }
.zona strong { color: var(--cor-texto); font-size: var(--texto-lg); }
.zona span { color: var(--cor-texto-suave); font-size: var(--texto-sm); }
.arquivo { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); border: 0; }
.escolhidos { margin: var(--espaco-4) 0 0; padding: 0; list-style: none; }
.escolhidos li { padding: var(--espaco-2) 0; border-bottom: 1px solid var(--cor-borda); font-family: var(--fonte-mono); font-size: var(--texto-sm); }
.acoes { display: flex; align-items: center; gap: var(--espaco-4); margin-top: var(--espaco-5); }
button, .botao { appearance: none; display: inline-flex; align-items: center; min-height: 44px; padding: 0 var(--espaco-5);
  border: 0; border-radius: var(--raio-m); background: var(--cor-acento); color: var(--cor-sobre-acento);
  font: var(--peso-medio) var(--texto-md)/1 var(--fonte-texto); text-decoration: none; cursor: pointer; }
button:hover, .botao:hover { background: var(--cor-acento-hover); color: var(--cor-sobre-acento); }
button:disabled { opacity: 0.72; cursor: progress; }
.estado { margin: 0; color: var(--cor-texto-suave); }
.nums { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--espaco-3); margin: var(--espaco-5) 0 0; padding: 0; list-style: none; }
.nums li { background: var(--cor-superficie); border: 1px solid var(--cor-borda); border-radius: var(--raio-m); padding: var(--espaco-4); box-shadow: var(--sombra-1); }
.nums b { display: block; font-size: var(--texto-xl); font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
.nums span { color: var(--cor-texto-suave); font-size: var(--texto-sm); }
.nums .marca-fn b, .nums .marca-er b { color: var(--cor-perigo); }
.nums .marca-av b { color: var(--cor-aviso); }
.nums .zero b { color: var(--cor-texto-suave); }
.painel { max-width: 1120px; }
.topo { display: flex; justify-content: space-between; align-items: flex-end; gap: var(--espaco-4); }
.topo .botao { flex: none; }
.kpis { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--espaco-3); margin: var(--espaco-5) 0 0; padding: 0; list-style: none; }
.kpis button { display: flex; flex-direction: column; align-items: flex-start; justify-content: center; gap: var(--espaco-1); width: 100%; min-height: 88px; padding: var(--espaco-4); border: 1px solid var(--cor-borda); border-radius: var(--raio-m); background: var(--cor-superficie); color: var(--cor-texto); box-shadow: var(--sombra-1); text-align: left; cursor: pointer; }
.kpis button b { font-size: var(--texto-2xl); font-variant-numeric: tabular-nums; letter-spacing: -0.03em; line-height: 1.1; }
.kpis button span { color: var(--cor-texto-suave); font-size: var(--texto-sm); font-weight: var(--peso-normal); }
.kpis button[aria-pressed="true"] { border-color: var(--cor-acento); box-shadow: 0 0 0 1px var(--cor-acento); }
.kpis .marca-fn b, .kpis .marca-er b { color: var(--cor-perigo); }
.kpis .marca-av b { color: var(--cor-aviso); }
.kpis .zero b { color: var(--cor-texto-suave); }
.grade { display: grid; grid-template-columns: 1.5fr 1fr; gap: var(--espaco-4); margin-top: var(--espaco-5); }
.cartao { min-width: 0; background: var(--cor-superficie); border: 1px solid var(--cor-borda); border-radius: var(--raio-m); padding: var(--espaco-4); }
.cartao h2, .secao h2 { margin: 0 0 var(--espaco-3); }
.linha-barra { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(72px, 1fr) auto; gap: var(--espaco-2); align-items: center; width: 100%; min-height: 36px; margin: 0; padding: 2px 0; border: 0; border-radius: var(--raio-p); background: transparent; color: var(--cor-texto); font: var(--peso-normal) var(--texto-sm)/1.3 var(--fonte-texto); text-align: left; cursor: pointer; }
.linha-barra.vol { cursor: default; }
.linha-barra .nome { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.linha-barra b { font-variant-numeric: tabular-nums; font-weight: var(--peso-medio); }
.trilha { display: block; height: 8px; border-radius: 999px; background: var(--cor-sutil); overflow: hidden; }
.barra { display: block; height: 100%; width: 100%; transform-origin: left center; border-radius: inherit; background: var(--cor-acento); }
.barra-erro, .barra-falso_negativo, .barra-error { background: var(--cor-perigo); }
.barra-aviso, .barra-warning { background: var(--cor-aviso); }
.barra-falso_positivo, .barra-outro, .barra-info, .barra-debug { background: var(--cor-texto-suave); }
.linha-barra.apagada { opacity: 0.38; }
.linha-barra[aria-pressed="true"] .nome { font-weight: var(--peso-medio); }
.linha-barra:hover { background: var(--cor-sutil); color: var(--cor-texto); }
.kpis button:hover { background: var(--cor-superficie); color: var(--cor-texto); }
.busca { display: flex; flex-wrap: wrap; gap: var(--espaco-3); align-items: center; margin-top: var(--espaco-3); }
.busca input { min-height: 36px; min-width: min(100%, 18rem); padding: 0 var(--espaco-3); border: 1px solid var(--cor-borda-forte); border-radius: var(--raio-p); background: var(--cor-superficie); color: var(--cor-texto); font: inherit; }
.legenda { margin: var(--espaco-2) 0 0; color: var(--cor-texto-suave); font-size: var(--texto-sm); }
.motivo { display: block; margin-top: var(--espaco-1); color: var(--cor-texto-suave); font-weight: var(--peso-normal); }
.secao { margin-top: var(--espaco-6); }
.filtrar { margin: var(--espaco-5) 0 0; color: var(--cor-texto-suave); font-size: var(--texto-sm); font-weight: var(--peso-medio); }
.filtros, .niveis { display: flex; flex-wrap: wrap; gap: var(--espaco-2); margin: var(--espaco-2) 0 0; padding: 0; list-style: none; }
.filtros button, .niveis button { min-height: 36px; padding: 0 var(--espaco-3); border: 1px solid var(--cor-borda); border-radius: 999px; background: var(--cor-superficie); color: var(--cor-texto); font-size: var(--texto-sm); }
.filtros button[aria-pressed="true"], .niveis button[aria-pressed="true"] { background: var(--cor-acento); color: var(--cor-sobre-acento); border-color: var(--cor-acento); }
.selo { display: inline-block; margin-left: var(--espaco-2); padding: 2px var(--espaco-2); border-radius: 999px; background: var(--cor-sutil); color: var(--cor-texto-suave); font-size: var(--texto-sm); font-weight: var(--peso-medio); }
.exportar { display: flex; flex-wrap: wrap; gap: var(--espaco-4); margin: var(--espaco-4) 0 0; }
[hidden] { display: none !important; }
.achado { margin: 0 0 var(--espaco-3); padding: var(--espaco-4); min-width: 0; background: var(--cor-superficie);
  border: 1px solid var(--cor-borda); border-left: 3px solid var(--cor-borda-forte); border-radius: var(--raio-m); }
.achado-erro, .achado-falso_negativo { border-left-color: var(--cor-perigo); }
.achado-aviso { border-left-color: var(--cor-aviso); }
.achado h3 { margin: 0; font-size: var(--texto-md); }
.achado small { color: var(--cor-texto-suave); font-weight: var(--peso-normal); }
.achado p { margin: var(--espaco-2) 0 0; }
.onde { margin: var(--espaco-3) 0 0; color: var(--cor-texto-suave); font-size: var(--texto-sm); }
.nomes { margin: var(--espaco-1) 0 0; padding: 0; list-style: none; max-height: 18rem; overflow: auto; }
.nomes li { color: var(--cor-texto-suave); font-family: var(--fonte-mono); font-size: var(--texto-sm); overflow-wrap: anywhere; }
.amostra { margin: var(--espaco-3) 0 0; min-width: 0; }
.amostra p { margin: 0 0 var(--espaco-1); color: var(--cor-texto-suave); font-family: var(--fonte-mono); font-size: var(--texto-sm); overflow-wrap: anywhere; }
pre { box-sizing: border-box; max-width: 100%; margin: 0; padding: var(--espaco-3); overflow-x: auto;
  white-space: pre-wrap; overflow-wrap: break-word;
  background: var(--cor-sutil); border-radius: var(--raio-p); font-family: var(--fonte-mono); font-size: var(--texto-sm); }
table { width: 100%; border-collapse: collapse; background: var(--cor-superficie); }
th, td { text-align: left; padding: var(--espaco-3) var(--espaco-4); border-bottom: 1px solid var(--cor-borda); vertical-align: top; }
th.n, td.n { text-align: right; font-variant-numeric: tabular-nums; }
.tabela { overflow: auto; border: 1px solid var(--cor-borda); border-radius: var(--raio-m); }
.erro { margin: var(--espaco-4) 0 var(--espaco-5); padding: var(--espaco-4); background: var(--cor-perigo-suave); color: var(--cor-texto); border-radius: var(--raio-m); }
.vazio { margin-top: var(--espaco-5); }
@media (max-width: 800px) {
  .nums, .kpis, .grade { grid-template-columns: 1fr 1fr; }
  .topo { flex-direction: column; align-items: flex-start; }
  h1 { font-size: var(--texto-xl); }
}
@media (max-width: 560px) { .kpis, .grade { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: no-preference) {
  .miolo { animation: entrar var(--dur-media) var(--curva-entrada); }
  .barra { animation: crescer var(--dur-media) var(--curva-entrada); }
  @keyframes entrar { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
  @keyframes crescer { from { transform: scaleX(0); } }
}
"""


def documento(titulo, miolo):
    return (
        "<!DOCTYPE html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{html.escape(titulo)}</title><style>{ESTILO}</style></head><body>{miolo}</body></html>"
    )


def _fmt(numero):
    return f"{numero:,}".replace(",", ".")


def _cortar_amostra(bloco):
    linhas = bloco.splitlines()
    if len(linhas) <= 8 and len(bloco) <= 900:
        return bloco
    pedaco = "\n".join(linhas[:8])
    if len(pedaco) > 900:
        corte = pedaco.rfind("\n", 0, 900)
        pedaco = pedaco[:corte if corte > 40 else 900]
    return pedaco.rstrip() + "\n…"


def _motivo_humano(motivo):
    if motivo.startswith("nível ") and " " not in motivo[len("nível "):]:
        nivel = motivo[len("nível "):]
        if nivel in ("error", "fatal", "critical"):
            return "O próprio log marca como erro."
        return f"O próprio log marca como {nivel}."
    return motivo if motivo.endswith(".") else motivo + "."


def _veredito(relatorio):
    achados = relatorio["achados"]
    if not achados:
        return "Nada a destacar neste conjunto."
    topo = max(achados, key=lambda a: a["contagem"])
    total = sum(a["contagem"] for a in achados)
    if len(achados) == 1:
        vezes = "1 vez" if topo["contagem"] == 1 else f"{_fmt(topo['contagem'])} vezes"
        return f"Tudo cai em {topo['titulo']}, {vezes}."
    if topo["contagem"] * 2 >= total:
        return f"O grosso é {topo['titulo']}: {_fmt(topo['contagem'])} de {_fmt(total)}."
    return f"{_fmt(total)} ocorrências em {len(achados)} grupos."


def _lista_arquivos(nomes):
    rotulo = "1 arquivo" if len(nomes) == 1 else f"{len(nomes)} arquivos"
    itens = "".join(f"<li>{html.escape(nome)}</li>" for nome in nomes)
    return f"<details class=\"arquivos\"><summary>{rotulo}</summary><ul class=\"nomes\">{itens}</ul></details>"


def _codigo(texto):
    t = html.escape(texto)
    for marca in (".", "\\", "/", "_"):
        t = t.replace(marca, marca + "\u200b")
    return t


def _bloco_amostra(am):
    quando = f"{am['quando']} · " if am["quando"] else ""
    return (
        "<div class=\"amostra\">"
        f"<p>{html.escape(quando + am['arquivo'] + ':' + str(am['linha']))}</p>"
        f"<pre>{_codigo(am['texto'])}</pre></div>"
    )


ROTULO_NIVEL = (
    ("error", "Erro"),
    ("warning", "Aviso"),
    ("info", "Info"),
    ("debug", "Debug"),
    ("outro", "Sem nível"),
)
SELO_NIVEL = dict(ROTULO_NIVEL)


ROTULO_CLASSE = (
    ("erro", "Erro", "erros", "marca-er"),
    ("aviso", "Aviso", "avisos", "marca-av"),
)
ROTULO_CLASSE_NOME = {chave: rotulo for chave, rotulo, _, _ in ROTULO_CLASSE}


def _pct(n, maior, log=False):
    if n <= 0 or maior <= 0:
        return 0.0
    if log:
        return math.log10(n + 1) / math.log10(maior + 1)
    return n / maior


def _trilha(pct, cor):
    return (
        f"<span class=\"trilha\"><span class=\"barra barra-{html.escape(cor)}\" "
        f"style=\"transform:scaleX({pct:.4f})\"></span></span>"
    )


def _contagem_nivel(relatorio):
    tot = {chave: 0 for chave, _ in ROTULO_NIVEL}
    for a in relatorio["achados"]:
        chave = a.get("nivel") or "outro"
        tot[chave] = tot.get(chave, 0) + a["contagem"]
    return tot


def _attrs_achado(a):
    nivel = a.get("nivel") or "outro"
    busca = html.escape((a["titulo"] + " " + a["motivo"]).lower(), quote=True)
    return (
        f"data-id=\"{html.escape(a['id'])}\" data-classe=\"{a['classe']}\" "
        f"data-nivel=\"{nivel}\" data-busca=\"{busca}\""
    )


def _barras_top(achados):
    if not achados:
        return "<section class=\"cartao\"><h2>O que mais aparece</h2><p class=\"vazio\">Nada a destacar neste conjunto.</p></section>"
    ordem = sorted(achados, key=lambda a: a["contagem"], reverse=True)
    visiveis = ordem[:12]
    maior = visiveis[0]["contagem"]
    linhas = []
    for a in visiveis:
        linhas.append(
            f"<button type=\"button\" class=\"linha-barra\" data-barra data-id-filtro {_attrs_achado(a)}>"
            f"<span class=\"nome\" title=\"{html.escape(a['titulo'], quote=True)}\">{html.escape(a['titulo'])}</span>"
            f"{_trilha(_pct(a['contagem'], maior), a['classe'])}"
            f"<b>{_fmt(a['contagem'])}</b></button>"
        )
    nota = ""
    if len(ordem) > len(visiveis):
        nota = f"<p class=\"legenda\">Mais {len(ordem) - len(visiveis)} grupos na tabela.</p>"
    return (
        "<section class=\"cartao\"><h2>O que mais aparece</h2>"
        + "".join(linhas) + nota + "</section>"
    )


def _volume(niveis):
    maior = max(niveis.values(), default=0)
    linhas = []
    for chave, rotulo in ROTULO_NIVEL:
        n = niveis.get(chave, 0)
        linhas.append(
            "<div class=\"linha-barra vol\">"
            f"<span class=\"nome\">{rotulo}</span>"
            f"{_trilha(_pct(n, maior, log=True), chave)}"
            f"<b>{_fmt(n)}</b></div>"
        )
    return (
        "<section class=\"cartao\"><h2>Volume do arquivo</h2>"
        "<p class=\"legenda\">Linha do arquivo, com ou sem problema. "
        "A barra compara a ordem de grandeza, para sem nível não esconder o erro.</p>"
        + "".join(linhas) + "</section>"
    )


def _kpis(resumo):
    itens = []
    for chave, rotulo, campo, marca in ROTULO_CLASSE:
        n = resumo[campo]
        zero = " zero" if not n else ""
        itens.append(
            f"<li class=\"{marca}{zero}\"><button type=\"button\" data-classe-filtro=\"{chave}\" aria-pressed=\"false\">"
            f"<b>{_fmt(n)}</b><span>{rotulo}</span></button></li>"
        )
    return "<ul class=\"kpis\">" + "".join(itens) + "</ul>"


def _filtros(relatorio):
    por_nivel = _contagem_nivel(relatorio)
    partes = [
        "<p class=\"filtrar\">Filtrar</p><ul class=\"filtros\">",
        "<li><button type=\"button\" data-classe-filtro=\"\" aria-pressed=\"true\">Tudo</button></li>",
    ]
    for chave, rotulo, _, _ in ROTULO_CLASSE:
        partes.append(
            f"<li><button type=\"button\" data-classe-filtro=\"{chave}\" aria-pressed=\"false\">{rotulo}</button></li>"
        )
    partes.append("</ul><ul class=\"niveis\">")
    for chave, rotulo in ROTULO_NIVEL:
        partes.append(
            f"<li><button type=\"button\" data-nivel-filtro=\"{chave}\" aria-pressed=\"false\">"
            f"{rotulo} <b>{_fmt(por_nivel.get(chave, 0))}</b></button></li>"
        )
    partes.append(
        "</ul><p class=\"legenda\">Nível do achado. O volume do arquivo, acima, conta outra coisa.</p>"
        "<label class=\"busca\">Buscar no título <input id=\"busca\" type=\"search\"></label>"
        "<p id=\"filtro-status\" class=\"legenda\"></p>"
        "<p id=\"vazio-filtro\" class=\"vazio\" hidden>Nada neste filtro.</p>"
    )
    return "".join(partes)


def _tabela(relatorio):
    if not relatorio["achados"]:
        return ""
    linhas = [
        "<div class=\"tabela\"><table><thead><tr>"
        "<th>Título</th><th>Classe</th><th>Nível</th><th class=\"n\">Vezes</th><th>Arquivos</th>"
        "</tr></thead><tbody>"
    ]
    for a in relatorio["achados"]:
        nivel = a.get("nivel") or "outro"
        amostras = a["amostras"]
        extra = ""
        if amostras:
            extra = _bloco_amostra(amostras[0])
            if len(amostras) > 1:
                extra += f"<details class=\"mais\"><summary>Mais {len(amostras) - 1} amostras</summary>"
                extra += "".join(_bloco_amostra(am) for am in amostras[1:])
                extra += "</details>"
        linhas.append(
            f"<tr data-linha {_attrs_achado(a)}>"
            f"<td><strong>{html.escape(a['titulo'])}</strong> "
            f"<span class=\"selo\">{html.escape(a['id'])}</span>"
            f"<span class=\"motivo\">{html.escape(_motivo_humano(a['motivo']))}</span>{extra}</td>"
            f"<td>{ROTULO_CLASSE_NOME[a['classe']]}</td>"
            f"<td>{html.escape(SELO_NIVEL.get(nivel, nivel))}</td>"
            f"<td class=\"n\">{_fmt(a['contagem'])}</td>"
            f"<td>{_lista_arquivos(a['arquivos'])}</td></tr>"
        )
    linhas.append("</tbody></table></div>")
    return "".join(linhas)


def _http(retornos):
    if not retornos:
        return ""
    maior = max(item["contagem"] for item in retornos)
    linhas = ["<section class=\"secao cartao\"><h2>Retornos HTTP</h2>"]
    for item in retornos:
        cor = "erro" if item["codigo"] >= 500 else "aviso" if item["codigo"] >= 400 else "info"
        linhas.append(
            "<div class=\"linha-barra vol\">"
            f"<span class=\"nome\">{item['codigo']} · {html.escape(item['como'])}</span>"
            f"{_trilha(_pct(item['contagem'], maior, log=True), cor)}"
            f"<b>{_fmt(item['contagem'])}</b></div>"
        )
    linhas.append("</section>")
    return "".join(linhas)


def _pulados(relatorio):
    pulados = [a for a in relatorio["arquivos"] if a["ignorado"]]
    if not pulados:
        return ""
    partes = ["<section class=\"secao\"><h2>Arquivos pulados</h2>"]
    if len(pulados) > 8:
        grupos = {}
        for a in pulados:
            grupos[a["ignorado"]] = grupos.get(a["ignorado"], 0) + 1
        nomes = {"vazio": "vazios", "binário": "binários", "arquivo grande demais": "grandes demais"}
        for motivo, n in grupos.items():
            partes.append(f"<p class=\"onde\">{_fmt(n)} arquivos {html.escape(nomes.get(motivo, motivo))}.</p>")
    partes.append("<ul class=\"nomes\">")
    for a in pulados:
        partes.append(f"<li>{html.escape(a['nome'])}: {html.escape(a['ignorado'])}</li>")
    partes.append("</ul></section>")
    return "".join(partes)


def _script_filtro():
    return """
<script>
(function () {
  var classe = "";
  var nivel = "";
  var escolhido = "";
  var busca = "";
  function casa(el, comId) {
    if (classe && el.getAttribute("data-classe") !== classe) return false;
    if (nivel && el.getAttribute("data-nivel") !== nivel) return false;
    if (comId && escolhido && el.getAttribute("data-id") !== escolhido) return false;
    if (busca && (el.getAttribute("data-busca") || "").indexOf(busca) < 0) return false;
    return true;
  }
  function aplicar() {
    var linhas = document.querySelectorAll("[data-linha]");
    var algum = false;
    var visiveis = 0;
    linhas.forEach(function (el) {
      var ok = casa(el, true);
      el.hidden = !ok;
      if (ok) { algum = true; visiveis += 1; }
    });
    document.querySelectorAll("[data-barra]").forEach(function (el) {
      var ok = casa(el, false);
      el.hidden = !ok;
      var ativo = !!(escolhido && el.getAttribute("data-id") === escolhido);
      el.classList.toggle("apagada", !!(escolhido && ok && !ativo));
      el.setAttribute("aria-pressed", ativo ? "true" : "false");
    });
    var vazio = document.getElementById("vazio-filtro");
    if (vazio) vazio.hidden = algum || linhas.length === 0;
    var status = document.getElementById("filtro-status");
    if (status) status.textContent = visiveis + " de " + linhas.length + " grupos";
  }
  document.querySelectorAll("[data-classe-filtro]").forEach(function (b) {
    b.addEventListener("click", function () {
      var valor = b.getAttribute("data-classe-filtro") || "";
      classe = (classe === valor && valor) ? "" : valor;
      escolhido = "";
      document.querySelectorAll("[data-classe-filtro]").forEach(function (o) {
        o.setAttribute("aria-pressed", (o.getAttribute("data-classe-filtro") || "") === classe ? "true" : "false");
      });
      aplicar();
    });
  });
  document.querySelectorAll("[data-nivel-filtro]").forEach(function (b) {
    b.addEventListener("click", function () {
      var valor = b.getAttribute("data-nivel-filtro") || "";
      nivel = nivel === valor ? "" : valor;
      document.querySelectorAll("[data-nivel-filtro]").forEach(function (o) {
        o.setAttribute("aria-pressed", o.getAttribute("data-nivel-filtro") === nivel ? "true" : "false");
      });
      aplicar();
    });
  });
  document.querySelectorAll("[data-id-filtro]").forEach(function (b) {
    b.addEventListener("click", function () {
      var valor = b.getAttribute("data-id") || "";
      escolhido = escolhido === valor ? "" : valor;
      aplicar();
    });
  });
  var campo = document.getElementById("busca");
  if (campo) campo.addEventListener("input", function () {
    busca = (campo.value || "").toLowerCase();
    aplicar();
  });
  aplicar();
})();
</script>
"""


def html_painel(relatorio, inicio=False, guarda=None, do_cache=False):
    r = relatorio["resumo"]
    href = f"/guarda/{guarda}/achados.xlsx" if guarda else "achados.xlsx"
    partes = ["<main class=\"miolo painel\">"]
    if inicio:
        partes.append("<p class=\"voltar\"><a href=\"/\">Nova análise</a></p>")
    partes.append(
        "<div class=\"topo\"><div>"
        "<p class=\"marca\">dev-flow · logs</p><h1>Análise de logs</h1>"
        f"<p class=\"veredito\">{html.escape(_veredito(relatorio))}</p>"
        "</div>"
        f"<a class=\"botao\" href=\"{html.escape(href, quote=True)}\">Baixar Excel</a></div>"
    )
    if do_cache:
        partes.append("<p class=\"resumo\">Leitura guardada neste computador. Não reli o arquivo.</p>")
    partes.append(
        f"<p class=\"resumo\">{_fmt(r['arquivos'])} arquivos, {_fmt(r['linhas'])} linhas. "
        "Os cartões contam ocorrência com problema.</p>"
    )
    partes.append(_kpis(r))
    partes.append("<div class=\"grade\">")
    partes.append(_barras_top(relatorio["achados"]))
    partes.append(_volume(r.get("niveis") or {}))
    partes.append("</div>")
    if relatorio["achados"]:
        partes.append("<section class=\"secao\">")
        partes.append(_filtros(relatorio))
        partes.append(_tabela(relatorio))
        partes.append("</section>")
    elif not relatorio["retornos"]:
        partes.append("<p class=\"vazio\">Nada a destacar neste conjunto.</p>")
    partes.append(_http(relatorio["retornos"]))
    partes.append(_pulados(relatorio))
    partes.append(_script_filtro())
    partes.append("</main>")
    return documento("Análise de logs", "".join(partes))


def gravar(relatorio, saida):
    os.makedirs(saida, exist_ok=True)
    json_path = os.path.join(saida, "relatorio.json")
    html_path = os.path.join(saida, "painel.html")
    xlsx_path = os.path.join(saida, "achados.xlsx")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_painel(relatorio))
    with open(xlsx_path, "wb") as f:
        f.write(planilha.xlsx_relatorio(relatorio))
    return json_path, html_path, xlsx_path


def _resumo_stdout(relatorio, html_path, xlsx_path):
    r = relatorio["resumo"]
    print(f"arquivos: {r['arquivos']}")
    print(f"linhas: {r['linhas']}")
    print(f"erros: {r['erros']}")
    print(f"avisos: {r['avisos']}")
    if r.get("niveis"):
        print(f"niveis: {r['niveis']}")
    print(f"painel: {html_path}")
    print(f"planilha: {xlsx_path}")


def main(argv):
    args = list(argv)
    estrito = False
    saida = "analise-logs"
    entradas = []
    i = 0
    while i < len(args):
        if args[i] == "--estrito":
            estrito = True
        elif args[i] == "--saida":
            i += 1
            if i >= len(args):
                print("falta o diretório de --saida", file=sys.stderr)
                return 1
            saida = args[i]
        elif args[i] in ("-h", "--help"):
            print(__doc__.strip())
            return 0
        else:
            entradas.append(args[i])
        i += 1
    if not entradas:
        print(__doc__.strip(), file=sys.stderr)
        return 1
    try:
        chave = guarda.chave_de_caminhos(entradas)
        relatorio = guarda.ler(chave)
        if relatorio is None:
            relatorio = analisar_entradas(entradas)
            guarda.guardar(chave, relatorio, [os.path.basename(c) for c in entradas])
        else:
            print("cache: hit")
    except EntradaInvalida as e:
        print(str(e), file=sys.stderr)
        return 1
    except (zipfile.BadZipFile, tarfile.TarError, gzip.BadGzipFile, OSError) as e:
        print(f"não foi possível ler a entrada: {e}", file=sys.stderr)
        return 1
    _, html_path, xlsx_path = gravar(relatorio, saida)
    _resumo_stdout(relatorio, html_path, xlsx_path)
    r = relatorio["resumo"]
    if estrito and r["erros"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
