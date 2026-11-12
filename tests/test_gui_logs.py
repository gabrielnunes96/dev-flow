import os
import sys
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
        cls.servidor = gui.criar_servidor(0)
        cls.thread = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.servidor.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.thread.join(timeout=3)

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
        self.assertIn("Nova análise", html)

    def test_dois_zips_no_mesmo_envio(self):
        status, html = self._post([
            ("um.zip", _zip("a.log", "ERROR IOException disco\n")),
            ("dois.zip", _zip("b.log", 'INFO status=200 body={"success":false}\n')),
        ])
        self.assertEqual(status, 200)
        self.assertIn("IOException", html)
        self.assertIn("success=false", html)
        self.assertIn("Falso negativo", html)

    def test_sem_arquivo(self):
        status, html = self._post([])
        self.assertEqual(status, 400)
        self.assertIn("nenhum arquivo", html)

    def test_nome_com_caminho_fica_no_basename(self):
        self.assertEqual(gui.nome_seguro("../fora.log"), "fora.log")
        self.assertEqual(gui.nome_seguro("pasta\\app.log"), "app.log")
