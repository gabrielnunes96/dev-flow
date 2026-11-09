import io
import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from apoio import ProjetoTemporario

import http_lote


class _Fake(BaseHTTPRequestHandler):
    recebidos = []

    def do_POST(self):
        corpo = self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0)
        _Fake.recebidos.append((self.path, self.headers.get("Authorization"), json.loads(corpo or b"null")))
        status = 200 if self.path == "/ok" else 400
        resposta = json.dumps({"mensagem": "feito", "claimId": "200002020654", "consumerKey": "segredo-123"}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(resposta)

    def log_message(self, *_):
        pass


class HttpLoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = HTTPServer(("127.0.0.1", 0), _Fake)
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.servidor.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()

    def executar(self, lote):
        perfil = {
            "nome": "X",
            "stacks": ["dotnet"],
            "validacao": {"tipo": "http", "base_url": self.url, "token": {"arquivo": "tk.txt"}, "mascarar": [r"segredo-\d+"]},
        }
        with ProjetoTemporario(perfil) as raiz:
            with open(os.path.join(raiz, "tk.txt"), "w") as f:
                f.write("TOKEN-XYZ")
            entrada, saida = sys.stdin, sys.stdout
            sys.stdin, sys.stdout = io.StringIO(json.dumps(lote)), io.StringIO()
            try:
                codigo = http_lote.main(["http_lote.py", "--tabela", "md"])
                return codigo, sys.stdout.getvalue()
            finally:
                sys.stdin, sys.stdout = entrada, saida

    def test_lote_com_esperado_token_mascara_e_tabela(self):
        _Fake.recebidos.clear()
        codigo, saida = self.executar(
            [{"nome": "ok", "metodo": "POST", "rota": "/ok", "corpo": {"a": 1}, "esperado": 200}, ["validacao", "POST", "/erro", {}]]
        )
        self.assertEqual(codigo, 0)
        self.assertEqual(_Fake.recebidos[0], ("/ok", "Bearer TOKEN-XYZ", {"a": 1}))
        self.assertNotIn("TOKEN-XYZ", saida)
        self.assertNotIn("segredo-123", saida)
        self.assertIn("== ok: HTTP 200", saida)
        self.assertIn("| ok | 200 | mensagem=feito; claimId=200002020654 |", saida)
        self.assertIn("| validacao | 400 |", saida)

    def test_falha_quando_status_difere_do_esperado(self):
        codigo, saida = self.executar([{"nome": "x", "metodo": "POST", "rota": "/erro", "corpo": {}, "esperado": 200}])
        self.assertEqual(codigo, 1)
        self.assertIn("FALHOU (esperado 200)", saida)


if __name__ == "__main__":
    unittest.main()
