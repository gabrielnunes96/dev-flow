import gzip
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

import apoio

sys.path.insert(0, os.path.join(apoio.RAIZ_REPO, "plugins", "logs", "scripts"))
import analisar  # noqa: E402

SCRIPT = os.path.join(apoio.RAIZ_REPO, "plugins", "logs", "scripts", "analisar.py")

LOG = """\
2026-03-01T10:00:00Z INFO request completed status=200 path=/api/pedido
2026-03-01T10:00:01Z ERROR NullReferenceException in PedidoService
   at PedidoService.Fechar
2026-03-01T10:00:02Z INFO GET /favicon.ico 404
2026-03-01T10:00:03Z INFO request completed status=200 path=/api/pedido body={"success":false,"error":"saldo"}
2026-03-01T10:00:04Z INFO error_count=0 component=api
2026-03-01T10:00:05Z WARN connection reset by peer path=/api/stream
2026-03-01T10:00:06Z INFO upstream_status=502 status=200 path=/api/proxy
{"ts":"2026-03-01T10:00:07Z","level":"info","msg":"done","status":500}
{"level":"info","error":"timeout na fila"}
"""


def classes(rel, classe):
    return [a for a in rel["achados"] if a["classe"] == classe]


def escrever(caminho, texto):
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)


def zipar(caminho, conteudo):
    with zipfile.ZipFile(caminho, "w") as z:
        for nome, texto in conteudo:
            z.writestr(nome, texto)


def tar_gz(caminho, conteudo):
    with tarfile.open(caminho, "w:gz") as t:
        for nome, texto in conteudo:
            dados = texto.encode("utf-8")
            info = tarfile.TarInfo(nome)
            info.size = len(dados)
            t.addfile(info, io.BytesIO(dados))


class ClassificarTests(unittest.TestCase):
    def test_conjunto_separa_as_classes(self):
        rel = analisar.montar([{"nome": "api.log", "texto": LOG}])
        self.assertEqual(rel["resumo"]["erros"], 1)
        self.assertGreaterEqual(rel["resumo"]["falsos_negativos"], 3)
        self.assertGreaterEqual(rel["resumo"]["falsos_positivos"], 3)
        erros = classes(rel, "erro")
        self.assertEqual(erros[0]["titulo"], "NullReferenceException")
        self.assertEqual(erros[0]["amostras"][0]["linha"], 2)
        self.assertIn("PedidoService.Fechar", erros[0]["amostras"][0]["texto"])
        fps = " ".join(a["motivo"] for a in classes(rel, "falso_positivo"))
        self.assertIn("/favicon.ico", fps)
        self.assertIn("contador de erro zerado", fps)
        self.assertIn("cliente fechou a conexão", fps)
        fns = classes(rel, "falso_negativo")
        motivos = " ".join(a["motivo"] for a in fns)
        self.assertIn("falha no corpo", motivos)
        self.assertIn("upstream 502", motivos)
        self.assertIn("esconde HTTP 500", motivos)
        self.assertIn("campo error", motivos)
        codigos = {(r["codigo"], r["como"]): r["contagem"] for r in rel["retornos"]}
        self.assertGreaterEqual(codigos[(200, "status")], 3)
        self.assertEqual(codigos[(502, "upstream")], 1)
        self.assertEqual(codigos[(500, "status")], 1)
        self.assertEqual(codigos[(404, "status")], 1)

    def test_http_200_saudavel_nao_vira_achado(self):
        rel = analisar.montar([{"nome": "a.log", "texto": "INFO status=200 path=/ok\n"}])
        self.assertEqual(rel["achados"], [])
        self.assertEqual(rel["retornos"], [{"codigo": 200, "como": "status", "contagem": 1}])

    def test_404_de_api_e_aviso_e_health_nao_e_ruido(self):
        rel = analisar.montar([{"nome": "a.log", "texto": "INFO GET /health 404\nINFO GET /api/pedido/1 422\n"}])
        self.assertEqual(rel["resumo"]["falsos_positivos"], 0)
        self.assertEqual(rel["resumo"]["avisos"], 2)

    def test_mesmo_erro_agrupa(self):
        texto = "ERROR TypeError: x\nERROR TypeError: x\n"
        rel = analisar.montar([{"nome": "a.log", "texto": texto}])
        self.assertEqual(len(classes(rel, "erro")), 1)
        self.assertEqual(classes(rel, "erro")[0]["contagem"], 2)

    def test_palavra_error_solta_nao_e_excecao(self):
        rel = analisar.montar([{"nome": "a.log", "texto": "INFO the word error is not a fault\n"}])
        self.assertEqual(rel["achados"], [])


class EntradaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="logs-")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_zip_e_tar_juntos(self):
        um = os.path.join(self.tmp, "um.log")
        with open(um, "w", encoding="utf-8") as f:
            f.write("ERROR IOException disco cheio\n")
        zp = os.path.join(self.tmp, "lote.zip")
        with zipfile.ZipFile(zp, "w") as z:
            z.writestr("a.log", "INFO status=200 path=/ok\n")
            z.writestr("b.log", "INFO status=200 path=/ok body={\"success\":false}\n")
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as t:
            dados = b"WARN connection reset by peer\n"
            info = tarfile.TarInfo("c.log")
            info.size = len(dados)
            t.addfile(info, io.BytesIO(dados))
        tar_path = os.path.join(self.tmp, "lote.tgz")
        with open(tar_path, "wb") as f:
            f.write(buf.getvalue())
        rel = analisar.analisar_entradas([um, zp, tar_path])
        nomes = {a["nome"] for a in rel["arquivos"]}
        self.assertEqual(nomes, {"um.log", "a.log", "b.log", "c.log"})
        self.assertEqual(rel["resumo"]["erros"], 1)
        self.assertEqual(rel["resumo"]["falsos_negativos"], 1)
        self.assertEqual(rel["resumo"]["falsos_positivos"], 1)

    def test_gzip_e_pasta(self):
        pasta = os.path.join(self.tmp, "pasta")
        os.makedirs(pasta)
        with gzip.open(os.path.join(pasta, "app.log.gz"), "wt", encoding="utf-8") as f:
            f.write("ERROR TypeError: quebrou\n")
        rel = analisar.analisar_entradas([pasta])
        self.assertEqual(rel["resumo"]["erros"], 1)
        self.assertTrue(rel["arquivos"][0]["nome"].endswith("app.log.gz"))

    def test_zip_com_caminho_inseguro_falha(self):
        zp = os.path.join(self.tmp, "mau.zip")
        with zipfile.ZipFile(zp, "w") as z:
            z.writestr("../fora.log", "ERROR TypeError: x\n")
        with self.assertRaises(analisar.EntradaInvalida):
            analisar.analisar_entradas([zp])

    def test_binario_e_pulado(self):
        caminho = os.path.join(self.tmp, "foto.png")
        with open(caminho, "wb") as f:
            f.write(b"\x89PNG\r\n\x00\x00")
        rel = analisar.analisar_entradas([caminho])
        self.assertEqual(rel["arquivos"][0]["ignorado"], "binário")
        self.assertEqual(rel["achados"], [])

    def _emitir(self, *entradas):
        saida = os.path.join(self.tmp, "saida")
        r = subprocess.run(
            [sys.executable, "-I", SCRIPT, *entradas, "--saida", saida],
            capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(os.listdir(saida)), ["painel.html", "relatorio.json"])
        with open(os.path.join(saida, "relatorio.json"), encoding="utf-8") as f:
            rel = json.load(f)
        with open(os.path.join(saida, "painel.html"), encoding="utf-8") as f:
            pagina = f.read()
        for chave, valor in rel["resumo"].items():
            self.assertIn(f"{chave}: {valor}", r.stdout)
        return rel, pagina

    def test_zip_com_um_arquivo(self):
        zp = os.path.join(self.tmp, "unico.zip")
        zipar(zp, [("pedido.log", "ERROR NullReferenceException in PedidoService\n")])
        rel, pagina = self._emitir(zp)
        self.assertEqual(rel["resumo"]["arquivos"], 1)
        self.assertEqual(rel["resumo"]["erros"], 1)
        self.assertEqual(rel["resumo"]["linhas"], 1)
        self.assertEqual(rel["arquivos"][0]["nome"], "pedido.log")
        self.assertIn("NullReferenceException", pagina)
        self.assertIn("pedido.log", pagina)

    def test_zip_com_varios_arquivos(self):
        zp = os.path.join(self.tmp, "varios.zip")
        zipar(zp, [
            ("a.log", "ERROR TypeError: um\n"),
            ("b.log", "ERROR IOException: dois\n"),
            ("c.log", "INFO status=200 path=/ok\n"),
            ("d.log", "INFO GET /favicon.ico 404\n"),
        ])
        rel, pagina = self._emitir(zp)
        self.assertEqual({a["nome"] for a in rel["arquivos"]}, {"a.log", "b.log", "c.log", "d.log"})
        self.assertEqual(rel["resumo"]["arquivos"], 4)
        self.assertEqual(rel["resumo"]["erros"], 2)
        self.assertEqual(rel["resumo"]["falsos_positivos"], 1)
        self.assertEqual(rel["resumo"]["falsos_negativos"], 0)
        self.assertIn("TypeError", pagina)
        self.assertIn("IOException", pagina)
        self.assertIn("/favicon.ico", pagina)

    def test_tar_gz_com_varios_arquivos(self):
        caminho = os.path.join(self.tmp, "lote.tar.gz")
        tar_gz(caminho, [
            ("n1.log", "ERROR TypeError: falhou\n"),
            ("n2.log", "ERROR TypeError: falhou\n"),
            ("n3.log", "WARN connection reset by peer path=/api/stream\n"),
        ])
        rel, pagina = self._emitir(caminho)
        self.assertEqual({a["nome"] for a in rel["arquivos"]}, {"n1.log", "n2.log", "n3.log"})
        self.assertEqual(rel["resumo"]["arquivos"], 3)
        self.assertEqual(rel["resumo"]["erros"], 2)
        self.assertEqual(rel["resumo"]["falsos_positivos"], 1)
        self.assertEqual(classes(rel, "erro")[0]["contagem"], 2)
        self.assertEqual(classes(rel, "erro")[0]["arquivos"], ["n1.log", "n2.log"])
        self.assertIn("n1.log", pagina)
        self.assertIn("n3.log", pagina)

    def test_dois_zips_somam_contagens(self):
        z1 = os.path.join(self.tmp, "erros.zip")
        z2 = os.path.join(self.tmp, "mais.zip")
        zipar(z1, [("api.log", "ERROR TypeError: falhou\nERROR TypeError: falhou\n")])
        zipar(z2, [(
            "web.log",
            "ERROR TypeError: falhou\n"
            "INFO request completed status=200 path=/api/pedido body={\"success\":false,\"error\":\"saldo\"}\n",
        )])
        rel, pagina = self._emitir(z1, z2)
        self.assertEqual({a["nome"] for a in rel["arquivos"]}, {"api.log", "web.log"})
        self.assertEqual(rel["resumo"]["arquivos"], 2)
        self.assertEqual(rel["resumo"]["linhas"], 4)
        self.assertEqual(rel["resumo"]["erros"], 3)
        self.assertEqual(rel["resumo"]["falsos_negativos"], 1)
        self.assertEqual(rel["resumo"]["falsos_positivos"], 0)
        self.assertEqual(classes(rel, "erro")[0]["contagem"], 3)
        self.assertEqual(classes(rel, "erro")[0]["arquivos"], ["api.log", "web.log"])
        codigos = {(r["codigo"], r["como"]): r["contagem"] for r in rel["retornos"]}
        self.assertEqual(codigos[(200, "status")], 1)
        self.assertIn("<small>(3)</small>", pagina)
        self.assertIn("api.log", pagina)
        self.assertIn("web.log", pagina)
        self.assertIn("Falso negativo", pagina)

    def test_arquivos_soltos_e_zip(self):
        solto1 = os.path.join(self.tmp, "solto1.log")
        solto2 = os.path.join(self.tmp, "solto2.log")
        escrever(solto1, "ERROR TypeError: falhou\n")
        escrever(solto2, "INFO error_count=0 component=api\n")
        zp = os.path.join(self.tmp, "pacote.zip")
        zipar(zp, [
            ("interno.log", "ERROR TypeError: falhou\n"),
            ("outro.log", "INFO status=200 path=/ok body={\"success\":false}\n"),
        ])
        rel, pagina = self._emitir(solto1, solto2, zp)
        self.assertEqual(
            {a["nome"] for a in rel["arquivos"]},
            {"solto1.log", "solto2.log", "interno.log", "outro.log"})
        self.assertEqual(rel["resumo"]["arquivos"], 4)
        self.assertEqual(rel["resumo"]["erros"], 2)
        self.assertEqual(rel["resumo"]["falsos_positivos"], 1)
        self.assertEqual(rel["resumo"]["falsos_negativos"], 1)
        self.assertEqual(classes(rel, "erro")[0]["contagem"], 2)
        self.assertEqual(classes(rel, "erro")[0]["arquivos"], ["solto1.log", "interno.log"])
        self.assertIn("solto1.log", pagina)
        self.assertIn("interno.log", pagina)
        self.assertIn("outro.log", pagina)

    def test_pasta_e_varios_arquivos_soltos(self):
        pasta = os.path.join(self.tmp, "pasta")
        os.makedirs(os.path.join(pasta, "sub"))
        escrever(os.path.join(pasta, "a.log"), "ERROR TypeError: falhou\n")
        escrever(os.path.join(pasta, "sub", "b.log"), "INFO status=500 path=/api/pedido\n")
        rel, pagina = self._emitir(pasta)
        self.assertEqual({a["nome"] for a in rel["arquivos"]}, {"a.log", "sub/b.log"})
        self.assertEqual(rel["resumo"]["arquivos"], 2)
        self.assertEqual(rel["resumo"]["erros"], 1)
        self.assertEqual(rel["resumo"]["falsos_negativos"], 1)
        self.assertIn("sub/b.log", pagina)

        s1 = os.path.join(self.tmp, "um.log")
        s2 = os.path.join(self.tmp, "dois.log")
        escrever(s1, "ERROR IOException: disco\n")
        escrever(s2, "INFO GET /robots.txt 404\n")
        rel, pagina = self._emitir(s1, s2)
        self.assertEqual({a["nome"] for a in rel["arquivos"]}, {"um.log", "dois.log"})
        self.assertEqual(rel["resumo"]["erros"], 1)
        self.assertEqual(rel["resumo"]["falsos_positivos"], 1)
        self.assertIn("IOException", pagina)
        self.assertIn("dois.log", pagina)

    def test_cli_grava_painel_e_estrito(self):
        log = os.path.join(self.tmp, "a.log")
        with open(log, "w", encoding="utf-8") as f:
            f.write(LOG)
        saida = os.path.join(self.tmp, "out")
        r = subprocess.run(
            [sys.executable, "-I", SCRIPT, log, "--saida", saida, "--estrito"],
            capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("falsos_negativos:", r.stdout)
        with open(os.path.join(saida, "relatorio.json"), encoding="utf-8") as f:
            rel = json.load(f)
        self.assertGreater(rel["resumo"]["falsos_negativos"], 0)
        with open(os.path.join(saida, "painel.html"), encoding="utf-8") as f:
            pagina = f.read()
        self.assertIn("Falso negativo", pagina)
        self.assertIn("NullReferenceException", pagina)
        self.assertIn("Retornos HTTP", pagina)
        self.assertNotIn("<script", pagina.lower())

    def test_cli_sem_entrada(self):
        r = subprocess.run([sys.executable, "-I", SCRIPT], capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 1)
