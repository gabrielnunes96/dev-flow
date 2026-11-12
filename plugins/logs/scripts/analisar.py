"""Analisa um conjunto de logs e separa erro, falso positivo e falso negativo.

Uso:
  python -I analisar.py <entrada>... [--saida DIR] [--estrito]

Entrada, num comando só: um arquivo, uma pasta, .gz, .zip, .tar, .tar.gz, .tgz ou .tar.bz2.
Um zip ou tar traz um log ou vários. Vários zips, tars e arquivos soltos juntos
saem num único relatório.
Sem --saida, grava ./analise-logs/relatorio.json e painel.html.
Código 0: análise concluída. 1: entrada inválida. 2: --estrito com erro ou falso negativo.
"""
import gzip
import html
import json
import os
import re
import sys
import tarfile
import zipfile

MAX_ARQUIVO = 20 * 1024 * 1024
MAX_TOTAL = 80 * 1024 * 1024
MAX_ARQUIVOS = 400
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

RE_NIVEL = re.compile(r"\b(FATAL|CRITICAL|ERROR|PANIC|WARN(?:ING)?|INFO|DEBUG|TRACE)\b", re.I)
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
    n = m.group(1).lower()
    return "warn" if n == "warning" else n


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
        nivel = nivel.lower()
        if nivel == "warning":
            nivel = "warn"
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
    """Devolve (achado ou None, lista de {codigo, como}). achado não inclui amostras."""
    extra = _do_json(texto)
    s = _sinais(texto, extra)
    retornos = []
    if s["status"] is not None:
        retornos.append({"codigo": s["status"], "como": "status"})
    if s["upstream"] is not None:
        retornos.append({"codigo": s["upstream"], "como": "upstream"})
    status, upstream, nivel = s["status"], s["upstream"], s["nivel"]
    falha_grave = (status is not None and status >= 500) or (upstream is not None and upstream >= 500)
    ruido_caminho = s["caminho"] in CAMINHOS_RUIDO and not falha_grave
    if ruido_caminho or (s["conexao"] and not falha_grave):
        motivo = "caminho de ruído " + s["caminho"] if ruido_caminho else "cliente fechou a conexão"
        titulo = s["caminho"] or "conexão encerrada pelo cliente"
        return _achado("falso_positivo", motivo, titulo, status), retornos
    if s["erro_vazio"] and not s["excecao"] and not s["sucesso_falso"] and not falha_grave and not s["timeout"]:
        return _achado("falso_positivo", "contador de erro zerado", "contador zerado", status), retornos
    if s["sucesso_falso"] and (status is None or status < 400):
        return _achado("falso_negativo", "HTTP 2xx com falha no corpo" if status else "corpo diz success=false",
                       "success=false", status), retornos
    if s["erro_campo"] and (nivel in NIVEL_BAIXO or nivel is None) and (status is None or status < 400):
        return _achado("falso_negativo", "campo error em nível baixo", "campo error", status), retornos
    if upstream is not None and upstream >= 500 and (status is None or status < 400):
        return _achado("falso_negativo", f"HTTP {status or '2xx'} com upstream {upstream}",
                       f"upstream {upstream}", status), retornos
    if status is not None and status >= 500 and nivel in NIVEL_BAIXO:
        return _achado("falso_negativo", f"nível {nivel} esconde HTTP {status}", f"HTTP {status}", status), retornos
    if s["excecao"] and nivel in NIVEL_BAIXO:
        return _achado("falso_negativo", f"exceção em nível {nivel}", s["tipo"] or "exceção", status), retornos
    if s["timeout"] and (nivel in NIVEL_BAIXO or nivel is None) and not falha_grave:
        return _achado("falso_negativo", "timeout fora do nível error", "timeout", status), retornos
    if status is not None and status >= 500:
        return _achado("erro", f"HTTP {status}", s["tipo"] or f"HTTP {status}", status), retornos
    if nivel in NIVEL_ALTO or (s["excecao"] and nivel not in NIVEL_BAIXO):
        return _achado("erro", "nível " + (nivel or "error"), s["tipo"] or (nivel or "error"), status), retornos
    if status is not None and 400 <= status < 500:
        return _achado("aviso", f"HTTP {status}", s["caminho"] or f"HTTP {status}", status), retornos
    return None, retornos


def _achado(classe, motivo, titulo, retorno):
    return {"classe": classe, "motivo": motivo, "titulo": titulo[:140], "retorno": retorno}


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
    for doc in documentos:
        if doc.get("ignorado"):
            arquivos.append({"nome": doc["nome"], "bytes": doc.get("bytes", 0), "linhas": 0, "ignorado": doc["ignorado"]})
            continue
        texto = doc.get("texto") or ""
        linhas = texto.splitlines()
        arquivos.append({"nome": doc["nome"], "bytes": doc.get("bytes", len(texto.encode("utf-8"))), "linhas": len(linhas), "ignorado": None})
        for numero, bloco in _blocos(linhas):
            achado, cods = classificar(bloco)
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
                    "texto": bloco[:MAX_TEXTO],
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
    if b"\x00" in data[:4096]:
        return {"nome": nome, "bytes": len(data), "ignorado": "binário"}
    try:
        texto = data.decode("utf-8")
    except UnicodeDecodeError:
        texto = data.decode("latin-1")
    return {"nome": nome, "bytes": len(data), "texto": texto}


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
                    achou = True
                    rel = os.path.relpath(cheio, caminho).replace("\\", "/")
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


def html_painel(relatorio):
    r = relatorio["resumo"]
    partes = [
        "<!DOCTYPE html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\">",
        "<title>Análise de logs</title><style>",
        "body{font:15px/1.45 sans-serif;margin:24px auto;max-width:980px;color:#1b1f24}",
        "h1{font-size:22px;margin:0 0 8px} h2{font-size:16px;margin:28px 0 8px}",
        "table{border-collapse:collapse;width:100%} th,td{border-bottom:1px solid #d0d7de;text-align:left;padding:6px 8px;vertical-align:top}",
        "td.n,th.n{text-align:right} pre{white-space:pre-wrap;background:#f6f8fa;padding:8px;margin:6px 0}",
        ".nums{display:flex;gap:16px;flex-wrap:wrap;margin:12px 0 4px}.nums div{min-width:120px}",
        ".nums b{display:block;font-size:20px}",
        "</style></head><body>",
        "<h1>Análise de logs</h1>",
        f"<p>{r['arquivos']} arquivos, {r['linhas']} linhas.</p><div class=\"nums\">",
        f"<div><b>{r['falsos_negativos']}</b>falsos negativos</div>",
        f"<div><b>{r['erros']}</b>erros</div>",
        f"<div><b>{r['avisos']}</b>avisos</div>",
        f"<div><b>{r['falsos_positivos']}</b>falsos positivos</div></div>",
    ]
    if relatorio["retornos"]:
        partes.append("<h2>Retornos HTTP</h2><table><tr><th>Código</th><th>Onde</th><th class=\"n\">Contagem</th></tr>")
        for item in relatorio["retornos"]:
            partes.append(
                f"<tr><td>{item['codigo']}</td><td>{html.escape(item['como'])}</td>"
                f"<td class=\"n\">{item['contagem']}</td></tr>")
        partes.append("</table>")
    rotulo = {"falso_negativo": "Falso negativo", "erro": "Erro", "aviso": "Aviso", "falso_positivo": "Falso positivo"}
    for classe, titulo in rotulo.items():
        lista = [a for a in relatorio["achados"] if a["classe"] == classe]
        if not lista:
            continue
        partes.append(f"<h2>{titulo}</h2>")
        for a in lista:
            partes.append(
                f"<h3>{html.escape(a['id'])} · {html.escape(a['titulo'])} "
                f"<small>({a['contagem']})</small></h3>")
            partes.append(f"<p>{html.escape(a['motivo'])}. Arquivos: {html.escape(', '.join(a['arquivos']))}.</p>")
            for am in a["amostras"]:
                quando = f"{am['quando']} · " if am["quando"] else ""
                partes.append(
                    f"<pre>{html.escape(quando + am['arquivo'] + ':' + str(am['linha']))}\n"
                    f"{html.escape(am['texto'])}</pre>")
    pulados = [a for a in relatorio["arquivos"] if a["ignorado"]]
    if pulados:
        partes.append("<h2>Arquivos pulados</h2><ul>")
        for a in pulados:
            partes.append(f"<li>{html.escape(a['nome'])}: {html.escape(a['ignorado'])}</li>")
        partes.append("</ul>")
    partes.append("</body></html>")
    return "".join(partes)


def gravar(relatorio, saida):
    os.makedirs(saida, exist_ok=True)
    json_path = os.path.join(saida, "relatorio.json")
    html_path = os.path.join(saida, "painel.html")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_painel(relatorio))
    return json_path, html_path


def _resumo_stdout(relatorio, html_path):
    r = relatorio["resumo"]
    print(f"arquivos: {r['arquivos']}")
    print(f"linhas: {r['linhas']}")
    print(f"falsos_negativos: {r['falsos_negativos']}")
    print(f"erros: {r['erros']}")
    print(f"avisos: {r['avisos']}")
    print(f"falsos_positivos: {r['falsos_positivos']}")
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
        relatorio = analisar_entradas(entradas)
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
