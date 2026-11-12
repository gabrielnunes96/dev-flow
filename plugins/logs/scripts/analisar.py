"""Analisa um conjunto de logs e separa erro, falso positivo e falso negativo.

Uso:
  python -I analisar.py <entrada>... [--saida DIR] [--estrito]

Entrada, num comando só: um arquivo, uma pasta, .gz, .zip, .tar, .tar.gz, .tgz ou .tar.bz2.
Um zip ou tar traz um log ou vários. Vários zips, tars e arquivos soltos juntos
saem num único relatório.
Sem --saida, grava ./analise-logs/relatorio.json e painel.html.
Código 0: análise concluída. 1: entrada inválida. 2: --estrito com erro ou falso negativo.
"""
import csv
import gzip
import html
import io
import json
import os
import re
import sys
import tarfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guarda  # noqa: E402

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
        motivo = "caminho de ruído " + s["caminho"] if ruido_caminho else "cliente fechou a conexão"
        titulo = s["caminho"] or "conexão encerrada pelo cliente"
        return sair(_achado("falso_positivo", motivo, titulo, status))
    if s["erro_vazio"] and not s["excecao"] and not s["sucesso_falso"] and not falha_grave and not s["timeout"]:
        return sair(_achado("falso_positivo", "contador de erro zerado", "contador zerado", status))
    if s["sucesso_falso"] and (status is None or status < 400):
        return sair(_achado("falso_negativo", "HTTP 2xx com falha no corpo" if status else "corpo diz success=false",
                            "success=false", status))
    if s["erro_campo"] and (nivel in NIVEL_BAIXO or nivel is None) and (status is None or status < 400):
        return sair(_achado("falso_negativo", "campo error em nível baixo", "campo error", status))
    if upstream is not None and upstream >= 500 and (status is None or status < 400):
        return sair(_achado("falso_negativo", f"HTTP {status or '2xx'} com upstream {upstream}",
                            f"upstream {upstream}", status))
    if status is not None and status >= 500 and nivel in NIVEL_BAIXO:
        return sair(_achado("falso_negativo", f"nível {nivel} esconde HTTP {status}", f"HTTP {status}", status))
    if s["excecao"] and nivel in NIVEL_BAIXO:
        return sair(_achado("falso_negativo", f"exceção em nível {nivel}", s["tipo"] or "exceção", status))
    if s["timeout"] and (nivel in NIVEL_BAIXO or nivel is None) and not falha_grave:
        return sair(_achado("falso_negativo", "timeout fora do nível error", "timeout", status))
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
    rank = {"falso_negativo": 0, "erro": 1, "aviso": 2, "falso_positivo": 3}
    chaves = sorted(ordem, key=lambda k: (rank[k[0]], -grupos[k]["contagem"], k[1]))
    achados = []
    for i, k in enumerate(chaves, 1):
        item = grupos[k]
        item["id"] = f"A{i}"
        achados.append(item)
    contagem = {c: sum(a["contagem"] for a in achados if a["classe"] == c)
                for c in ("erro", "falso_negativo", "falso_positivo", "aviso")}
    return {
        "resumo": {
            "arquivos": len(arquivos),
            "linhas": sum(a["linhas"] for a in arquivos),
            "erros": contagem["erro"],
            "falsos_negativos": contagem["falso_negativo"],
            "falsos_positivos": contagem["falso_positivo"],
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
.filtros, .niveis { display: flex; flex-wrap: wrap; gap: var(--espaco-2); margin: var(--espaco-4) 0 0; padding: 0; list-style: none; }
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
.nomes { margin: var(--espaco-1) 0 0; padding: 0; list-style: none; }
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
@media (max-width: 700px) { .nums { grid-template-columns: 1fr 1fr; } h1 { font-size: var(--texto-xl); } }
@media (prefers-reduced-motion: no-preference) {
  .miolo { animation: entrar var(--dur-media) var(--curva-entrada); }
  @keyframes entrar { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
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
    itens = "".join(f"<li>{html.escape(nome)}</li>" for nome in nomes[:4])
    if len(nomes) > 4:
        itens += f"<li>e mais {len(nomes) - 4}</li>"
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


def _filtros(relatorio):
    niveis = (relatorio.get("resumo") or {}).get("niveis") or {}
    partes = ["<ul class=\"niveis\">"]
    for chave, rotulo in ROTULO_NIVEL:
        n = niveis.get(chave, 0)
        if n == 0 and chave not in ("error", "warning", "info"):
            continue
        partes.append(
            f"<li><button type=\"button\" data-nivel-filtro=\"{chave}\" aria-pressed=\"false\">"
            f"{rotulo} <b>{_fmt(n)}</b></button></li>")
    partes.append("</ul><ul class=\"filtros\">")
    partes.append("<li><button type=\"button\" data-classe-filtro=\"\" aria-pressed=\"true\">Tudo</button></li>")
    for chave, rotulo in (
        ("falso_negativo", "Falso negativo"),
        ("erro", "Erro"),
        ("aviso", "Aviso"),
        ("falso_positivo", "Falso positivo"),
    ):
        partes.append(
            f"<li><button type=\"button\" data-classe-filtro=\"{chave}\" aria-pressed=\"false\">{rotulo}</button></li>")
    partes.append("</ul><p id=\"vazio-filtro\" class=\"vazio\" hidden>Nada neste filtro.</p>")
    return "".join(partes)


def _script_filtro():
    return """
<script>
(function () {
  var classe = "";
  var nivel = "";
  function aplicar() {
    var algum = false;
    var cards = document.querySelectorAll(".achado");
    cards.forEach(function (el) {
      var ok = (!classe || el.getAttribute("data-classe") === classe) && (!nivel || el.getAttribute("data-nivel") === nivel);
      el.hidden = !ok;
      if (ok) algum = true;
    });
    document.querySelectorAll("h2[data-classe]").forEach(function (h) {
      var visivel = false;
      var n = h.nextElementSibling;
      while (n && n.classList && n.classList.contains("achado")) {
        if (!n.hidden) visivel = true;
        n = n.nextElementSibling;
      }
      h.hidden = !visivel;
    });
    var vazio = document.getElementById("vazio-filtro");
    if (vazio) vazio.hidden = algum || cards.length === 0;
  }
  document.querySelectorAll("[data-classe-filtro]").forEach(function (b) {
    b.addEventListener("click", function () {
      classe = b.getAttribute("data-classe-filtro") || "";
      document.querySelectorAll("[data-classe-filtro]").forEach(function (o) {
        o.setAttribute("aria-pressed", o === b ? "true" : "false");
      });
      aplicar();
    });
  });
  document.querySelectorAll("[data-nivel-filtro]").forEach(function (b) {
    b.addEventListener("click", function () {
      var valor = b.getAttribute("data-nivel-filtro") || "";
      nivel = nivel === valor ? "" : valor;
      document.querySelectorAll("[data-nivel-filtro]").forEach(function (o) {
        o.setAttribute("aria-pressed", o === b && nivel ? "true" : "false");
      });
      aplicar();
    });
  });
})();
</script>
"""


def html_painel(relatorio, inicio=False, guarda=None, do_cache=False):
    r = relatorio["resumo"]
    partes = ["<main class=\"miolo\">"]
    if inicio:
        partes.append("<p class=\"voltar\"><a href=\"/\">Nova análise</a></p>")
    partes.append("<p class=\"marca\">dev-flow · logs</p><h1>Análise de logs</h1>")
    partes.append(f"<p class=\"veredito\">{html.escape(_veredito(relatorio))}</p>")
    if do_cache:
        partes.append("<p class=\"resumo\">Leitura guardada neste computador. Não reli o arquivo.</p>")
    if guarda:
        partes.append(
            "<p class=\"exportar\">"
            f"<a href=\"/guarda/{guarda}/relatorio.json\">Baixar JSON</a>"
            f"<a href=\"/guarda/{guarda}/achados.csv\">Baixar CSV</a>"
            f"<a href=\"/guarda/{guarda}/painel.html\">Baixar HTML</a>"
            "</p>")
    partes.append(
        f"<p class=\"resumo\">{_fmt(r['arquivos'])} arquivos, {_fmt(r['linhas'])} linhas.</p>"
        "<ul class=\"nums\">"
        f"<li class=\"marca-fn{' zero' if not r['falsos_negativos'] else ''}\"><b>{_fmt(r['falsos_negativos'])}</b><span>falsos negativos</span></li>"
        f"<li class=\"marca-er{' zero' if not r['erros'] else ''}\"><b>{_fmt(r['erros'])}</b><span>erros</span></li>"
        f"<li class=\"marca-av{' zero' if not r['avisos'] else ''}\"><b>{_fmt(r['avisos'])}</b><span>avisos</span></li>"
        f"<li class=\"{'zero' if not r['falsos_positivos'] else ''}\"><b>{_fmt(r['falsos_positivos'])}</b><span>falsos positivos</span></li>"
        "</ul>"
    )
    partes.append(_filtros(relatorio))
    if relatorio["retornos"]:
        partes.append("<h2>Retornos HTTP</h2><div class=\"tabela\"><table><tr><th>Código</th><th>Onde</th><th class=\"n\">Contagem</th></tr>")
        for item in relatorio["retornos"]:
            partes.append(
                f"<tr><td>{item['codigo']}</td><td>{html.escape(item['como'])}</td>"
                f"<td class=\"n\">{_fmt(item['contagem'])}</td></tr>")
        partes.append("</table></div>")
    rotulo = {"falso_negativo": "Falso negativo", "erro": "Erro", "aviso": "Aviso", "falso_positivo": "Falso positivo"}
    teve = False
    for classe, titulo in rotulo.items():
        lista = [a for a in relatorio["achados"] if a["classe"] == classe]
        if not lista:
            continue
        teve = True
        partes.append(f"<h2 data-classe=\"{classe}\">{titulo}</h2>")
        for a in lista:
            principal = " achado-principal" if a is lista[0] and classe in ("falso_negativo", "erro") else ""
            nivel = a.get("nivel") or "outro"
            partes.append(
                f"<article class=\"achado achado-{classe}{principal}\" data-classe=\"{classe}\" data-nivel=\"{nivel}\">"
                f"<h3>{html.escape(a['id'])} · {html.escape(a['titulo'])} "
                f"<small>({a['contagem']})</small> "
                f"<span class=\"selo\">{html.escape(SELO_NIVEL.get(nivel, nivel))}</span></h3>"
                f"<p>{html.escape(_motivo_humano(a['motivo']))}</p>"
                f"{_lista_arquivos(a['arquivos'])}")
            amostras = a["amostras"]
            if amostras:
                partes.append(_bloco_amostra(amostras[0]))
            if len(amostras) > 1:
                partes.append(f"<details class=\"mais\"><summary>Mais {len(amostras) - 1} amostras</summary>")
                for am in amostras[1:]:
                    partes.append(_bloco_amostra(am))
                partes.append("</details>")
            partes.append("</article>")
    if not teve and not relatorio["retornos"]:
        partes.append("<p class=\"vazio\">Nada a destacar neste conjunto.</p>")
    pulados = [a for a in relatorio["arquivos"] if a["ignorado"]]
    if pulados:
        partes.append("<h2>Arquivos pulados</h2>")
        if len(pulados) <= 8:
            partes.append("<ul class=\"escolhidos\">")
            for a in pulados:
                partes.append(f"<li>{html.escape(a['nome'])}: {html.escape(a['ignorado'])}</li>")
            partes.append("</ul>")
        else:
            grupos = {}
            for a in pulados:
                grupos[a["ignorado"]] = grupos.get(a["ignorado"], 0) + 1
            nomes = {"vazio": "vazios", "binário": "binários", "arquivo grande demais": "grandes demais"}
            for motivo, n in grupos.items():
                partes.append(
                    f"<p class=\"onde\">{_fmt(n)} arquivos {html.escape(nomes.get(motivo, motivo))}.</p>")
    partes.append(_script_filtro())
    partes.append("</main>")
    return documento("Análise de logs", "".join(partes))


def csv_achados(relatorio):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "classe", "nivel", "contagem", "titulo", "motivo", "arquivos"])
    for a in relatorio.get("achados") or []:
        w.writerow([
            a.get("id", ""),
            a.get("classe", ""),
            a.get("nivel", ""),
            a.get("contagem", 0),
            a.get("titulo", ""),
            a.get("motivo", ""),
            " ".join(a.get("arquivos") or []),
        ])
    return buf.getvalue()


def gravar(relatorio, saida):
    os.makedirs(saida, exist_ok=True)
    json_path = os.path.join(saida, "relatorio.json")
    html_path = os.path.join(saida, "painel.html")
    csv_path = os.path.join(saida, "achados.csv")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_painel(relatorio))
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        f.write(csv_achados(relatorio))
    return json_path, html_path


def _resumo_stdout(relatorio, html_path):
    r = relatorio["resumo"]
    print(f"arquivos: {r['arquivos']}")
    print(f"linhas: {r['linhas']}")
    print(f"falsos_negativos: {r['falsos_negativos']}")
    print(f"erros: {r['erros']}")
    print(f"avisos: {r['avisos']}")
    print(f"falsos_positivos: {r['falsos_positivos']}")
    if r.get("niveis"):
        print(f"niveis: {r['niveis']}")
    print(f"painel: {html_path}")


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
    _, html_path = gravar(relatorio, saida)
    _resumo_stdout(relatorio, html_path)
    r = relatorio["resumo"]
    if estrito and (r["erros"] or r["falsos_negativos"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
