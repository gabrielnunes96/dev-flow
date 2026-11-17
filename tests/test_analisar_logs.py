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
import guarda  # noqa: E402
import planilha  # noqa: E402

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
        self.assertEqual(rel["resumo"]["erros"], 5)
        self.assertEqual(rel["resumo"]["avisos"], 0)
        self.assertNotIn("falsos_negativos", rel["resumo"])
        self.assertNotIn("falsos_positivos", rel["resumo"])
        erros = classes(rel, "erro")
        self.assertEqual(len(erros), 5)
        nulo = next(a for a in erros if a["titulo"] == "NullReferenceException")
        self.assertEqual(nulo["amostras"][0]["linha"], 2)
        self.assertIn("PedidoService.Fechar", nulo["amostras"][0]["texto"])
        motivos = " ".join(a["motivo"] for a in erros)
        self.assertNotIn("favicon", motivos)
        self.assertNotIn("contador", motivos)
        self.assertNotIn("conexão", motivos)
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
        self.assertEqual(rel["resumo"]["avisos"], 2)

    def test_mesmo_erro_agrupa(self):
        texto = "ERROR TypeError: x\nERROR TypeError: x\n"
        rel = analisar.montar([{"nome": "a.log", "texto": texto}])
        self.assertEqual(len(classes(rel, "erro")), 1)
        self.assertEqual(classes(rel, "erro")[0]["contagem"], 2)

    def test_erro_em_portugues_sem_exception_entra(self):
        texto = (
            "06/11/2026 15:47:01 - Status das Threads concluídas:\n"
            "06/11/2026 15:47:01 - Thread #21: RanToCompletion\n"
            "06/11/2026 16:45:19 - Erro ao gerar law, retorno StatusCode diferente 200. StatusCode -> OK\n"
            "06/11/2026 16:45:19 - Erro geral API_CRIPTOGRAFIA_CARTAO: "
            "Api de Criptografia retornou falta de sucesso em sua transação..\n"
            "06/11/2026 16:45:30 - Status das Threads concluídas:\n"
        )
        rel = analisar.montar([{"nome": "sonda.txt", "texto": texto}])
        self.assertEqual(rel["resumo"]["erros"], 2)
        titulos = [a["titulo"] for a in rel["achados"]]
        self.assertIn("Erro ao gerar law, retorno StatusCode diferente 200. StatusCode -> OK", titulos)
        self.assertTrue(any("API_CRIPTOGRAFIA_CARTAO" in t for t in titulos))
        pagina = analisar.html_painel(rel)
        self.assertIn("API_CRIPTOGRAFIA_CARTAO", pagina)
        self.assertNotIn("RanToCompletion", pagina)
        self.assertEqual(rel["resumo"]["niveis"]["error"], 2)
        self.assertEqual(sum(rel["resumo"]["niveis"].values()), 5)
        for achado in rel["achados"]:
            self.assertEqual(achado["classe"], "erro")
            self.assertEqual(achado["nivel"], "error")

    def test_niveis_contam_cada_bloco_e_o_painel_filtra(self):
        texto = "\n".join([
            "ERROR TypeError: x",
            "AVISO disco quase cheio",
            "INFO status=200 path=/ok",
            "DEBUG detalhe interno",
            "linha sem nivel",
        ]) + "\n"
        rel = analisar.montar([{"nome": "a.log", "texto": texto}])
        self.assertEqual(rel["resumo"]["niveis"], {
            "error": 1, "warning": 1, "info": 1, "debug": 1, "outro": 1,
        })
        self.assertEqual([a["classe"] for a in rel["achados"]], ["erro"])
        pagina = analisar.html_painel(rel)
        self.assertIn("data-classe", pagina)
        self.assertIn("data-nivel", pagina)
        self.assertIn("Filtrar", pagina)
        self.assertIn('data-classe="erro"', pagina)
        self.assertIn('data-nivel="error"', pagina)
        for chave in ("error", "warning", "info", "debug", "outro"):
            self.assertIn(f'data-nivel-filtro="{chave}"', pagina)
        for chave in ("", "erro", "aviso"):
            self.assertIn(f'data-classe-filtro="{chave}"', pagina)
        self.assertIn("Sem nível", pagina)
        self.assertIn("Volume do arquivo", pagina)
        dados = planilha.xlsx_relatorio(rel)
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            niveis = z.read("xl/worksheets/sheet3.xml").decode("utf-8")
            achados = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn("Sem nível", niveis)
        self.assertIn(">1<", niveis)
        self.assertIn("TypeError", achados)
        self.assertNotIn("linha sem nivel", achados)
        self.assertIn("O que mais aparece", pagina)
        self.assertIn("Baixar Excel", pagina)
        self.assertNotIn("Baixar JSON", pagina)
        self.assertNotIn("Baixar CSV", pagina)

    def test_palavra_error_solta_nao_e_excecao(self):
        rel = analisar.montar([{"nome": "a.log", "texto": "INFO the word error is not a fault\n"}])
        self.assertEqual(rel["achados"], [])


class EntradaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="logs-")
        self._env_cache = os.environ.get("DEVFLOW_LOGS_CACHE")
        os.environ["DEVFLOW_LOGS_CACHE"] = os.path.join(self.tmp, "cache")

    def tearDown(self):
        if self._env_cache is None:
            os.environ.pop("DEVFLOW_LOGS_CACHE", None)
        else:
            os.environ["DEVFLOW_LOGS_CACHE"] = self._env_cache
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
        self.assertEqual(rel["resumo"]["erros"], 2)
        self.assertEqual(rel["resumo"]["avisos"], 0)

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

    def test_tar_com_caminho_inseguro_falha(self):
        caminho = os.path.join(self.tmp, "mau.tar")
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as t:
            dados = b"ERROR TypeError: x\n"
            info = tarfile.TarInfo("../fora.log")
            info.size = len(dados)
            t.addfile(info, io.BytesIO(dados))
        with open(caminho, "wb") as f:
            f.write(buf.getvalue())
        with self.assertRaises(analisar.EntradaInvalida):
            analisar.analisar_entradas([caminho])

    def test_tar_com_mais_de_400_arquivos(self):
        caminho = os.path.join(self.tmp, "muitos.tar")
        with tarfile.open(caminho, "w") as t:
            for i in range(450):
                dados = b"INFO status=200 path=/ok\n" if i else b"ERROR TypeError: falhou\n"
                info = tarfile.TarInfo(f"l{i}.log")
                info.size = len(dados)
                t.addfile(info, io.BytesIO(dados))
        rel = analisar.analisar_entradas([caminho])
        self.assertEqual(rel["resumo"]["arquivos"], 450)
        self.assertEqual(rel["resumo"]["erros"], 1)

    def test_painel_resume_lista_longa_de_arquivos(self):
        pasta = os.path.join(self.tmp, "muitos")
        os.makedirs(pasta)
        for i in range(8):
            escrever(os.path.join(pasta, f"a{i}.log"), "ERROR TypeError: falhou\n")
        pagina = analisar.html_painel(analisar.analisar_entradas([pasta]))
        self.assertNotRegex(pagina, r"e mais \d+")
        self.assertIn("Tudo cai em TypeError, 8 vezes.", pagina)
        for i in range(8):
            self.assertIn(f"a{i}.log", pagina)
        self.assertIn('class="n">8<', pagina)

    def test_metadado_de_macos_nao_entra(self):
        caminho = os.path.join(self.tmp, "mac.tar")
        with tarfile.open(caminho, "w") as t:
            for nome, dados in (
                ("._app.log", b"\x00\x00"),
                ("__MACOSX/app.log", b"\x00"),
                (".DS_Store", b"\x00"),
                ("app.log", b"ERROR TypeError: falhou\n"),
            ):
                info = tarfile.TarInfo(nome)
                info.size = len(dados)
                t.addfile(info, io.BytesIO(dados))
        rel = analisar.analisar_entradas([caminho])
        self.assertEqual([a["nome"] for a in rel["arquivos"]], ["app.log"])
        self.assertEqual(rel["resumo"]["erros"], 1)
        self.assertNotIn("Arquivos pulados", analisar.html_painel(rel))

    def test_muitos_vazios_viram_uma_linha(self):
        caminho = os.path.join(self.tmp, "vazios.tar")
        with tarfile.open(caminho, "w") as t:
            for i in range(9):
                dados = b"\x00" * 8
                info = tarfile.TarInfo(f"v{i}.log")
                info.size = len(dados)
                t.addfile(info, io.BytesIO(dados))
            dados = b"ERROR TypeError: falhou\n"
            info = tarfile.TarInfo("app.log")
            info.size = len(dados)
            t.addfile(info, io.BytesIO(dados))
        rel = analisar.analisar_entradas([caminho])
        pagina = analisar.html_painel(rel)
        self.assertEqual(sum(1 for a in rel["arquivos"] if a["ignorado"] == "vazio"), 9)
        self.assertIn("9 arquivos vazios.", pagina)
        self.assertIn("v0.log", pagina)
        self.assertIn("v8.log", pagina)

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
        self.assertEqual(sorted(os.listdir(saida)), ["achados.xlsx", "painel.html", "relatorio.json"])
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
        self.assertEqual(rel["resumo"]["avisos"], 0)
        self.assertIn("TypeError", pagina)
        self.assertIn("IOException", pagina)
        self.assertNotIn("/favicon.ico", pagina)

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
        self.assertEqual(rel["resumo"]["avisos"], 0)
        self.assertEqual(classes(rel, "erro")[0]["contagem"], 2)
        self.assertEqual(classes(rel, "erro")[0]["arquivos"], ["n1.log", "n2.log"])
        self.assertIn("n1.log", pagina)
        self.assertNotIn("n3.log", pagina)

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
        self.assertEqual(rel["resumo"]["erros"], 4)
        self.assertEqual(rel["resumo"]["avisos"], 0)
        self.assertEqual(classes(rel, "erro")[0]["contagem"], 3)
        self.assertEqual(classes(rel, "erro")[0]["arquivos"], ["api.log", "web.log"])
        codigos = {(r["codigo"], r["como"]): r["contagem"] for r in rel["retornos"]}
        self.assertEqual(codigos[(200, "status")], 1)
        self.assertIn('class="n">3<', pagina)
        self.assertIn("api.log", pagina)
        self.assertIn("web.log", pagina)
        self.assertNotIn("Falso negativo", pagina)
        self.assertNotIn("Falso positivo", pagina)

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
        self.assertEqual(rel["resumo"]["erros"], 3)
        self.assertEqual(rel["resumo"]["avisos"], 0)
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
        self.assertEqual(rel["resumo"]["erros"], 2)
        self.assertEqual(rel["resumo"]["avisos"], 0)
        self.assertIn("sub/b.log", pagina)

        s1 = os.path.join(self.tmp, "um.log")
        s2 = os.path.join(self.tmp, "dois.log")
        escrever(s1, "ERROR IOException: disco\n")
        escrever(s2, "INFO GET /robots.txt 404\n")
        rel, pagina = self._emitir(s1, s2)
        self.assertEqual({a["nome"] for a in rel["arquivos"]}, {"um.log", "dois.log"})
        self.assertEqual(rel["resumo"]["erros"], 1)
        self.assertEqual(rel["resumo"]["avisos"], 0)
        self.assertIn("IOException", pagina)
        self.assertNotIn("dois.log", pagina)

    def test_cli_grava_painel_e_estrito(self):
        log = os.path.join(self.tmp, "a.log")
        with open(log, "w", encoding="utf-8") as f:
            f.write(LOG)
        saida = os.path.join(self.tmp, "out")
        r = subprocess.run(
            [sys.executable, "-I", SCRIPT, log, "--saida", saida, "--estrito"],
            capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("erros:", r.stdout)
        self.assertNotIn("falsos_negativos:", r.stdout)
        with open(os.path.join(saida, "relatorio.json"), encoding="utf-8") as f:
            rel = json.load(f)
        self.assertGreater(rel["resumo"]["erros"], 0)
        with open(os.path.join(saida, "painel.html"), encoding="utf-8") as f:
            pagina = f.read()
        self.assertNotIn("Falso negativo", pagina)
        self.assertNotIn("Falso positivo", pagina)
        self.assertIn("NullReferenceException", pagina)
        self.assertIn("Retornos HTTP", pagina)
        self.assertIn("data-nivel-filtro", pagina)
        script = pagina.lower().split("<script", 1)[1]
        self.assertNotIn("nullreference", script)
        self.assertNotIn("pedido", script)

    def test_cli_sem_entrada(self):
        r = subprocess.run([sys.executable, "-I", SCRIPT], capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 1)

    def test_cache_vazio_desliga(self):
        os.environ["DEVFLOW_LOGS_CACHE"] = ""
        self.assertIsNone(guarda.diretorio())
        guarda.guardar("a" * 64, {"resumo": {"erros": 1}}, ["a.log"])
        self.assertIsNone(guarda.ler("a" * 64))
        self.assertEqual(guarda.limpar(), 0)

    def test_limpar_apaga_so_a_guarda(self):
        raiz = os.path.join(self.tmp, "guarda")
        os.makedirs(raiz)
        chave = "ab" * 32
        outra = "cd" * 32
        guarda.guardar(chave, {"resumo": {"erros": 2}, "achados": []}, ["api.log"], raiz=raiz)
        guarda.guardar(outra, {"resumo": {"erros": 0}}, ["b.log"], raiz=raiz)
        with open(os.path.join(raiz, "nota.txt"), "w", encoding="utf-8") as f:
            f.write("ficar")
        self.assertEqual(len(guarda.listar(raiz)), 2)
        self.assertEqual(guarda.limpar(raiz), 2)
        self.assertEqual(guarda.listar(raiz), [])
        self.assertIsNone(guarda.ler(chave, raiz))
        self.assertIsNone(guarda.ler(outra, raiz))
        with open(os.path.join(raiz, "nota.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "ficar")
        self.assertEqual(guarda.limpar(raiz), 0)

    def test_cache_nao_reanalisa(self):
        log = os.path.join(self.tmp, "a.log")
        escrever(log, "ERROR TypeError: quebrou\n")
        chamadas = {"n": 0}
        original = analisar.analisar_entradas

        def contar(caminhos):
            chamadas["n"] += 1
            return original(caminhos)

        analisar.analisar_entradas = contar
        try:
            buf = io.StringIO()
            antigo = sys.stdout
            sys.stdout = buf
            try:
                codigo = analisar.main([log, "--saida", os.path.join(self.tmp, "s1")])
            finally:
                sys.stdout = antigo
            self.assertEqual(codigo, 0)
            self.assertNotIn("cache: hit", buf.getvalue())
            self.assertEqual(chamadas["n"], 1)
            chave = guarda.chave_de_caminhos([log])
            guardado = guarda.ler(chave)
            self.assertIsNotNone(guardado)
            self.assertEqual(guardado["resumo"]["erros"], 1)
            buf = io.StringIO()
            antigo = sys.stdout
            sys.stdout = buf
            try:
                codigo = analisar.main([log, "--saida", os.path.join(self.tmp, "s2")])
            finally:
                sys.stdout = antigo
            self.assertEqual(codigo, 0)
            self.assertEqual(chamadas["n"], 1)
            self.assertIn("cache: hit", buf.getvalue())
            self.assertEqual(guarda.ler(chave)["achados"][0]["titulo"], "TypeError")
        finally:
            analisar.analisar_entradas = original
