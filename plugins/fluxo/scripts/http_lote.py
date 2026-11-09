"""Executa um lote de chamadas HTTP contra a aplicação local (validacao.base_url do perfil) e monta a tabela do card.

Uso: python -I http_lote.py [--limite N] [--tabela html|md] < lote.json

Lote: lista de objetos {"nome", "metodo", "rota", "corpo"?, "esperado"?} ou de listas [nome, metodo, rota, corpo].
- O JWT, se houver, vem de validacao.token.arquivo e nunca é impresso.
- validacao.mascarar (lista de regex) mascara trechos da resposta (ConsumerKey, senhas) antes de imprimir.
- Com "esperado" (status HTTP), cada linha sai com OK/FALHOU e o código de saída é 1 se alguma falhar.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfil as perfil_mod  # noqa: E402


def normalizar(item):
    if isinstance(item, list):
        nome, metodo, rota, *resto = item
        return {"nome": nome, "metodo": metodo, "rota": rota, "corpo": resto[0] if resto else None}
    return item


def mascarar(texto, padroes):
    for rx in padroes:
        texto = re.sub(rx, "***", texto)
    return texto


def chamar(base_url, item, token=None, timeout=180):
    corpo = item.get("corpo")
    cabecalhos = {"Content-Type": "application/json", **(item.get("cabecalhos") or {})}
    if token:
        cabecalhos["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        base_url.rstrip("/") + item["rota"],
        data=None if corpo is None else json.dumps(corpo).encode("utf-8"),
        headers=cabecalhos,
        method=item["metodo"].upper(),
    )
    inicio = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, texto = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        status, texto = e.code, e.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as e:
        status, texto = 0, f"sem resposta: {e}"
    return status, texto, time.time() - inicio


def resumo_resposta(texto, limite=160):
    """Mensagem e IDs relevantes do JSON (campos mensagem/message/id*), ou o começo do texto."""
    try:
        j = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return texto[:limite]
    partes = []

    def andar(o, prof=0):
        if prof > 3 or len(partes) >= 4:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (str, int)) and (k.lower() in ("mensagem", "message", "status") or k.lower().endswith("id")):
                    partes.append(f"{k}={v}")
                elif isinstance(v, (dict, list)):
                    andar(v, prof + 1)
        elif isinstance(o, list) and o:
            andar(o[0], prof + 1)

    andar(j)
    return ("; ".join(partes) or json.dumps(j, ensure_ascii=False))[:limite]


def tabela(linhas, formato):
    if formato == "md":
        out = ["| Chamada | Status | Resultado |", "| --- | --- | --- |"]
        out += [f"| {n} | {s} | {r.replace('|', '/')} |" for n, s, r in linhas]
        return "\n".join(out)
    out = ['<table border="1" cellpadding="4">', "<tr><th>Chamada</th><th>Status</th><th>Resultado</th></tr>"]
    esc = lambda t: str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")  # noqa: E731
    out += [f"<tr><td>{esc(n)}</td><td>{esc(s)}</td><td>{esc(r)}</td></tr>" for n, s, r in linhas]
    return "\n".join(out + ["</table>"])


def _opcao(argv, nome, padrao):
    return argv[argv.index(nome) + 1] if nome in argv and argv.index(nome) + 1 < len(argv) else padrao


def main(argv):
    limite = int(_opcao(argv, "--limite", "600"))
    formato = _opcao(argv, "--tabela", "html")
    raiz, perfil = perfil_mod.carregar()
    validacao = perfil.get("validacao") or {}
    base_url = os.environ.get("FLUXO_BASE_URL") or validacao.get("base_url")
    if not base_url:
        sys.exit("validacao.base_url ausente no perfil.")
    token = None
    arq_token = perfil_mod.obter(perfil, "validacao.token.arquivo")
    if arq_token:
        caminho = os.path.join(raiz, arq_token)
        if not os.path.exists(caminho):
            sys.exit(f"token ausente ({arq_token}); rode o script de token do perfil antes.")
        with open(caminho, encoding="utf-8") as f:
            token = f.read().strip()
    padroes = validacao.get("mascarar") or []

    linhas, falhas = [], 0
    for item in map(normalizar, json.load(sys.stdin)):
        status, texto, dur = chamar(base_url, item, token)
        texto = mascarar(texto, padroes)
        esperado = item.get("esperado")
        veredito = "" if esperado is None else (" OK" if status == esperado else f" FALHOU (esperado {esperado})")
        falhas += bool(esperado is not None and status != esperado)
        print(f"== {item['nome']}: HTTP {status} ({dur:.1f}s){veredito}")
        print(texto[:limite] + (" ...[truncado]" if len(texto) > limite else ""))
        linhas.append((item["nome"], status, resumo_resposta(texto)))
    print("\n" + tabela(linhas, formato))
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
