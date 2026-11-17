import os
import re
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import zipfile
import io

import apoio

sys.path.insert(0, os.path.join(apoio.RAIZ_REPO, "plugins", "logs", "scripts"))
import gui  # noqa: E402


def _corpo(arquivos):
    limite = "----logsform"
    blocos = []
    for nome, dados in arquivos:
        blocos.append(
            f"--{limite}\r\nContent-Disposition: form-data; name=\"arquivo\"; filename=\"{nome}\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n".encode()
            + dados
            + b"\r\n"
        )
    blocos.append(f"--{limite}--\r\n".encode())
    return limite, b"".join(blocos)


def _zip(nome_interno, texto):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(nome_interno, texto)
    return buf.getvalue()


class GuiLogsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._cache = tempfile.mkdtemp()
        cls._env_cache = os.environ.get("DEVFLOW_LOGS_CACHE")
        os.environ["DEVFLOW_LOGS_CACHE"] = cls._cache
        cls.servidor = gui.criar_servidor(0)
        cls.thread = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.servidor.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.thread.join(timeout=3)
        if cls._env_cache is None:
            os.environ.pop("DEVFLOW_LOGS_CACHE", None)
        else:
            os.environ["DEVFLOW_LOGS_CACHE"] = cls._env_cache
        shutil.rmtree(cls._cache, ignore_errors=True)

    def _post(self, arquivos):
        limite, corpo = _corpo(arquivos)
        pedido = urllib.request.Request(
            self.base + "/analisar",
            data=corpo,
            headers={"Content-Type": f"multipart/form-data; boundary={limite}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(pedido) as resp:
                return resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8")

    def _get(self, caminho):
        try:
            with urllib.request.urlopen(self.base + caminho) as resp:
                return resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8")

    def test_pagina_inicial(self):
        with urllib.request.urlopen(self.base + "/") as resp:
            html = resp.read().decode("utf-8")
        self.assertIn("vários zips", html)
        self.assertIn("Solte os logs", html)
        self.assertIn("prefers-color-scheme", html)
        self.assertIn('multiple', html)

    def test_um_arquivo(self):
        status, html = self._post([("api.log", b"ERROR TypeError: quebrou\n")])
        self.assertEqual(status, 200)
        self.assertIn("TypeError", html)
        self.assertIn("api.log", html)
        self.assertNotIn("1-api.log", html)
        self.assertIn("Nova análise", html)

    def test_dois_zips_no_mesmo_envio(self):
        status, html = self._post([
            ("um.zip", _zip("a.log", "ERROR IOException disco\n")),
            ("dois.zip", _zip("b.log", 'INFO status=200 body={"success":false}\n')),
        ])
        self.assertEqual(status, 200)
        self.assertIn("IOException", html)
        self.assertIn("success=false", html)
        self.assertNotIn("Falso negativo", html)
        self.assertNotIn("Falso positivo", html)

    def test_sem_arquivo(self):
        status, html = self._post([])
        self.assertEqual(status, 400)
        self.assertIn("nenhum arquivo", html)

    def test_nome_com_caminho_fica_no_basename(self):
        self.assertEqual(gui.nome_seguro("../fora.log"), "fora.log")
        self.assertEqual(gui.nome_seguro("pasta\\app.log"), "app.log")

    def test_reenvio_vem_da_guarda_e_o_excel_baixa(self):
        linha = "Erro falhou ao gravar o pedido\n"
        status, html = self._post([("api.log", linha.encode())])
        self.assertEqual(status, 200)
        self.assertNotIn("Leitura guardada neste computador", html)
        self.assertIn("data-classe", html)
        self.assertIn("data-nivel", html)
        self.assertIn("Filtrar", html)
        self.assertIn("Volume do arquivo", html)
        self.assertNotIn("achados.csv", html)
        self.assertNotIn("Baixar JSON", html)
        achado = re.search(r"/guarda/([0-9a-f]{64})/achados\.xlsx", html)
        self.assertIsNotNone(achado)
        chave = achado.group(1)
        with urllib.request.urlopen(self.base + f"/guarda/{chave}/achados.xlsx") as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("spreadsheetml", resp.headers.get("Content-Type", ""))
            dados = resp.read()
        self.assertTrue(dados.startswith(b"PK"))
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            aba = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn("Erro falhou ao gravar o pedido", aba)
        status, html = self._get(f"/guarda/{chave}/achados.csv")
        self.assertEqual(status, 404)
        status, de_novo = self._post([("api.log", linha.encode())])
        self.assertEqual(status, 200)
        self.assertIn("Leitura guardada neste computador", de_novo)
        status, inicio = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("Guardadas neste computador", inicio)
        self.assertIn(f"/guarda/{chave}", inicio)
        self.assertIn("api.log", inicio)

    def test_limpar_a_lista_guardada(self):
        linha = "ERROR LimparListaMarker: sumiu\n"
        status, html = self._post([("limpar-lista.log", linha.encode())])
        self.assertEqual(status, 200)
        self.assertNotIn("Leitura guardada neste computador", html)
        status, inicio = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("Guardadas neste computador", inicio)
        self.assertIn("Limpar lista", inicio)
        self.assertIn("limpar-lista.log", inicio)
        self.assertIn("/guarda/limpar", inicio)
        self.assertIn("Apagar as análises guardadas neste computador?", inicio)
        pedido = urllib.request.Request(self.base + "/guarda/limpar", data=b"", method="POST")

        class NaoSegue(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise urllib.error.HTTPError(newurl, code, msg, headers, fp)

        try:
            urllib.request.build_opener(NaoSegue).open(pedido)
            self.fail("esperava redirecionar")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 303)
            self.assertEqual(e.headers.get("Location"), "/?limpas=1")
        status, limpa = self._get("/?limpas=1")
        self.assertEqual(status, 200)
        self.assertIn("foram apagadas", limpa)
        self.assertNotIn("Guardadas neste computador", limpa)
        self.assertNotIn("limpar-lista.log", limpa)
        status, inicio = self._get("/")
        self.assertNotIn("foram apagadas", inicio)
        status, html = self._post([("limpar-lista.log", linha.encode())])
        self.assertEqual(status, 200)
        self.assertNotIn("Leitura guardada neste computador", html)
        status, html = self._get("/guarda/limpar")
        self.assertEqual(status, 404)

    def test_rejeita_chave_que_nao_e_hex(self):
        for caminho in ("/guarda/nao-e-hex", "/guarda/" + "g" * 64, "/guarda/" + "A" * 64):
            status, html = self._get(caminho)
            self.assertEqual(status, 404, caminho)
            self.assertIn("não encontrado", html)
        status, html = self._get("/guarda/" + "ab" * 32)
        self.assertEqual(status, 404)
        self.assertIn("não encontrado", html)
