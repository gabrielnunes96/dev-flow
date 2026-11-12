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

PAGINA = analisar.documento("Análise de logs", """
<main class="miolo">
<p class="marca">dev-flow · logs</p>
<h1>Análise de logs</h1>
<p class="lead">Um arquivo, vários arquivos, um zip ou tar, ou vários zips e tars juntos.
A leitura é uma só e o painel sai embaixo.</p>
<form action="/analisar" method="post" enctype="multipart/form-data">
<label class="zona" for="arquivo">
<strong>Solte os logs aqui</strong>
<span>ou escolha no computador · .log, .txt, .gz, .zip, .tar, .tar.gz</span>
<input class="arquivo" id="arquivo" type="file" name="arquivo" multiple>
</label>
<ul class="escolhidos" id="lista" hidden></ul>
<div class="acoes">
<button type="submit">Analisar</button>
<p class="estado" id="estado" hidden>Lendo o conjunto e separando erro de ruído.</p>
</div>
</form>
</main>
<script>
const entrada = document.querySelector("#arquivo");
const lista = document.querySelector("#lista");
const zona = document.querySelector(".zona");
const form = document.querySelector("form");
const botao = document.querySelector("button");
const estado = document.querySelector("#estado");
function escapar(texto) {
  return texto.replace(/[&<>"]/g, function (c) {
    return {"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;"}[c];
  });
}
function mostrar(arquivos) {
  if (!arquivos.length) { lista.hidden = true; lista.textContent = ""; return; }
  const visiveis = Array.prototype.slice.call(arquivos, 0, 6);
  let html = visiveis.map(function (f) { return "<li>" + escapar(f.name) + "</li>"; }).join("");
  if (arquivos.length > 6) html += "<li>e mais " + (arquivos.length - 6) + "</li>";
  lista.innerHTML = html;
  lista.hidden = false;
}
entrada.addEventListener("change", function () { mostrar(entrada.files); });
["dragenter", "dragover"].forEach(function (nome) {
  zona.addEventListener(nome, function (e) { e.preventDefault(); zona.classList.add("sobre"); });
});
["dragleave", "drop"].forEach(function (nome) {
  zona.addEventListener(nome, function (e) { e.preventDefault(); zona.classList.remove("sobre"); });
});
zona.addEventListener("drop", function (e) {
  const dt = new DataTransfer();
  Array.prototype.forEach.call(e.dataTransfer.files, function (f) { dt.items.add(f); });
  entrada.files = dt.files;
  mostrar(entrada.files);
});
form.addEventListener("submit", function () {
  if (!entrada.files.length) return;
  botao.disabled = true;
  botao.textContent = "Analisando…";
  estado.hidden = false;
});
</script>
""")


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
    miolo = (
        "<main class=\"miolo\"><p class=\"marca\">dev-flow · logs</p>"
        "<h1>Não deu para analisar</h1>"
        f"<p class=\"erro\">{analisar.html.escape(mensagem)}</p>"
        "<p><a class=\"botao\" href=\"/\">Voltar</a></p></main>"
    )
    return analisar.documento("Análise de logs", miolo)


def html_resultado(relatorio):
    return analisar.html_painel(relatorio, inicio=True)


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
