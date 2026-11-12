"""Interface local da análise de logs. Só biblioteca padrão.

Uso:
  python -I gui.py [--porta 8765] [--sem-navegador]

Abre http://127.0.0.1:8765/ . Aceita um arquivo, vários, um zip ou tar,
ou vários zips e tars no mesmo envio. O painel sai na mesma página.
"""
import os
import re
import shutil
import sys
import tarfile
import tempfile
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analisar  # noqa: E402

PAGINA = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Análise de logs</title>
<style>
body{font:15px/1.45 sans-serif;margin:32px auto;max-width:720px;color:#1b1f24}
h1{font-size:22px;margin:0 0 8px}
form{margin-top:20px}
input[type=file]{display:block;margin:12px 0}
button{font:inherit;padding:6px 14px}
</style>
</head>
<body>
<h1>Análise de logs</h1>
<p>Um arquivo, vários arquivos, um zip ou tar, ou vários zips e tars juntos.
A leitura é uma só e o painel sai embaixo.</p>
<form action="/analisar" method="post" enctype="multipart/form-data">
<input type="file" name="arquivo" multiple>
<button type="submit">Analisar</button>
</form>
</body>
</html>
"""


def nome_seguro(bruto):
    base = os.path.basename((bruto or "").replace("\\", "/"))
    if not base or base in (".", ".."):
        raise analisar.EntradaInvalida("nome de arquivo inválido")
    return base


def partes_multipart(content_type, body):
    if not content_type or "multipart/form-data" not in content_type.lower():
        raise analisar.EntradaInvalida("envio inválido")
    m = re.search(r"boundary=([^;]+)", content_type, re.I)
    if not m:
        raise analisar.EntradaInvalida("envio inválido")
    limite = m.group(1).strip().strip('"').encode("utf-8", "replace")
    pedacos = body.split(b"--" + limite)
    arquivos = []
    for pedaco in pedacos:
        if pedaco in (b"", b"--") or pedaco.startswith(b"--"):
            continue
        if pedaco.startswith(b"\r\n"):
            pedaco = pedaco[2:]
        if pedaco.endswith(b"\r\n"):
            pedaco = pedaco[:-2]
        cabeca, sep, dados = pedaco.partition(b"\r\n\r\n")
        if not sep:
            continue
        texto = cabeca.decode("utf-8", "replace")
        achado = re.search(r'filename="([^"]*)"', texto)
        if not achado:
            achado = re.search(r"filename\*=UTF-8''([^;\r\n]+)", texto, re.I)
        if not achado or not achado.group(1):
            continue
        nome = nome_seguro(achado.group(1))
        if dados:
            arquivos.append((nome, dados))
    if not arquivos:
        raise analisar.EntradaInvalida("nenhum arquivo")
    if len(arquivos) > analisar.MAX_ARQUIVOS:
        raise analisar.EntradaInvalida("conjunto grande demais")
    return arquivos


def analisar_uploads(arquivos):
    pasta = tempfile.mkdtemp(prefix="logs-gui-")
    try:
        caminhos = []
        for i, (nome, dados) in enumerate(arquivos, 1):
            if len(dados) > analisar.MAX_ARQUIVO:
                raise analisar.EntradaInvalida("arquivo grande demais")
            destino = os.path.join(pasta, f"{i}-{nome_seguro(nome)}")
            with open(destino, "wb") as f:
                f.write(dados)
            caminhos.append(destino)
        return analisar.analisar_entradas(caminhos)
    finally:
        shutil.rmtree(pasta, ignore_errors=True)


def html_erro(mensagem):
    return (
        "<!DOCTYPE html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\"><title>Análise de logs</title></head>"
        f"<body><p><a href=\"/\">Voltar</a></p><p>{analisar.html.escape(mensagem)}</p></body></html>"
    )


def html_resultado(relatorio):
    pagina = analisar.html_painel(relatorio)
    return pagina.replace("<body>", '<body><p><a href="/">Nova análise</a></p>', 1)


class Pedido(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?", 1)[0] != "/":
            self._enviar(404, html_erro("não encontrado"))
            return
        self._enviar(200, PAGINA)

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/analisar":
            self._enviar(404, html_erro("não encontrado"))
            return
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            tamanho = 0
        if tamanho > analisar.MAX_TOTAL:
            self._enviar(413, html_erro("envio grande demais"))
            return
        corpo = self.rfile.read(tamanho)
        try:
            relatorio = analisar_uploads(partes_multipart(self.headers.get("Content-Type", ""), corpo))
        except analisar.EntradaInvalida as e:
            self._enviar(400, html_erro(str(e)))
            return
        except (zipfile.BadZipFile, tarfile.TarError, OSError):
            self._enviar(400, html_erro("não foi possível ler a entrada"))
            return
        self._enviar(200, html_resultado(relatorio))

    def log_message(self, fmt, *args):
        return

    def _enviar(self, codigo, corpo):
        dados = corpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)


def criar_servidor(porta):
    return ThreadingHTTPServer(("127.0.0.1", porta), Pedido)


def main(argv):
    porta = 8765
    abrir = True
    i = 0
    while i < len(argv):
        if argv[i] == "--sem-navegador":
            abrir = False
        elif argv[i] == "--porta":
            i += 1
            if i >= len(argv):
                print("falta o número de --porta", file=sys.stderr)
                return 1
            porta = int(argv[i])
        elif argv[i] in ("-h", "--help"):
            print(__doc__.strip())
            return 0
        else:
            print(__doc__.strip(), file=sys.stderr)
            return 1
        i += 1
    servidor = criar_servidor(porta)
    url = f"http://{servidor.server_address[0]}:{servidor.server_address[1]}/"
    print(url, flush=True)
    if abrir:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
