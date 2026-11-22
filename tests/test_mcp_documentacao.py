"""MCP de documentação: catálogo datado (referencias/documentacao.md) e gerador de configuração por host."""
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

from apoio import FLUXO

sys.path.insert(0, os.path.join(FLUXO, "scripts"))
import mcp_documentacao as mcp  # noqa: E402
import perfil  # noqa: E402


def _rodar(*args):
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(io.StringIO()):
        codigo = mcp.main(list(args))
    return codigo, saida.getvalue()


class CatalogoTests(unittest.TestCase):  # CA-5
    def test_catalogo_datado_com_fonte_e_cobrindo_toda_stack(self):
        with open(mcp.CATALOGO, encoding="utf-8") as f:
            texto = f.read()
        self.assertRegex(texto, r"<!-- dev-flow:conhecimento revisado_em=\d{4}-\d{2}-\d{2} produtos=- -->")
        fontes = texto.split("## Fontes", 1)[1]
        itens = mcp.ler_catalogo()
        self.assertGreaterEqual(len(re.findall(r"https://", fontes)), len(itens))
        for item in itens:
            self.assertIn(item["nome"].split("-")[-1], fontes, item["nome"])
        cobertas = set().union(*(i["stacks"] for i in itens))
        self.assertTrue("*" in cobertas or perfil.STACKS - {"outra"} <= cobertas)
        self.assertIn("busca na web", texto)

    def test_procedimento_e_iniciar_apontam_o_catalogo(self):
        for rel in (("referencias", "conhecimento.md"), ("skills", "iniciar", "SKILL.md"), ("referencias", "hosts.md")):
            with open(os.path.join(FLUXO, *rel), encoding="utf-8") as f:
                texto = f.read()
            self.assertIn("documentacao.md", texto, rel)
            if rel[0] == "skills":
                self.assertIn("mcp_documentacao.py", texto)


class GeradorTests(unittest.TestCase):  # CA-6
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="mcp-")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _perfil(self, stacks):
        os.makedirs(os.path.join(self.dir, ".claude"))
        with open(os.path.join(self.dir, ".claude", "projeto.json"), "w", encoding="utf-8") as f:
            json.dump({"nome": "x", "stacks": stacks}, f)

    def test_formato_por_host_e_filtro_por_stack(self):
        self._perfil(["dotnet", "sql"])
        codigo, saida = _rodar("--host", "claude", "--dir", self.dir)
        self.assertEqual(codigo, 0)
        servidores = json.loads(saida)["mcpServers"]
        self.assertEqual(set(servidores), {"microsoft-learn", "context7"})
        self.assertEqual(servidores["microsoft-learn"], {"type": "http", "url": "https://learn.microsoft.com/api/mcp"})
        _, saida = _rodar("--host", "cursor", "--stack", "python")
        servidores = json.loads(saida)["mcpServers"]
        self.assertEqual(set(servidores), {"context7"})
        self.assertNotIn("type", servidores["context7"])
        self.assertNotIn("headers", servidores["context7"])

    def test_chave_so_por_variavel(self):
        _, saida = _rodar("--host", "cursor", "--stack", "go", "--com-chave")
        self.assertEqual(json.loads(saida)["mcpServers"]["context7"]["headers"],
                         {"Authorization": "Bearer ${env:CONTEXT7_API_KEY}"})
        _, saida = _rodar("--host", "claude", "--stack", "dotnet", "--com-chave")
        servidores = json.loads(saida)["mcpServers"]
        self.assertEqual(servidores["context7"]["headers"], {"Authorization": "Bearer ${CONTEXT7_API_KEY}"})
        self.assertNotIn("headers", servidores["microsoft-learn"])

    def test_sem_perfil_ou_catalogo_mal_formado_sai_com_1(self):
        antes = os.environ.pop("CLAUDE_PROJECT_DIR", None)
        try:
            self.assertEqual(_rodar("--host", "claude", "--dir", self.dir)[0], 1)
        finally:
            if antes is not None:
                os.environ["CLAUDE_PROJECT_DIR"] = antes
        for invalido in ([], {"stacks": "dotnet"}, {"stacks": [{"a": 1}]}):
            shutil.rmtree(os.path.join(self.dir, ".claude"), ignore_errors=True)
            os.makedirs(os.path.join(self.dir, ".claude"))
            with open(os.path.join(self.dir, ".claude", "projeto.json"), "w", encoding="utf-8") as f:
                json.dump(invalido, f)
            self.assertEqual(_rodar("--host", "claude", "--dir", self.dir)[0], 1, invalido)
        ruim = os.path.join(self.dir, "doc.md")
        with open(ruim, "w", encoding="utf-8") as f:
            f.write("## Catálogo\n| `x` | http://inseguro | não | — | * | — |\n")
        with self.assertRaises(mcp.Erro):
            mcp.ler_catalogo(ruim)
        with open(ruim, "w", encoding="utf-8") as f:
            f.write("# nada\n")
        with self.assertRaises(mcp.Erro):
            mcp.ler_catalogo(ruim)
        linha = "| `x` | https://a.org/mcp | não | — | * | — |\n"
        for texto in ("## Catálogo\n| MCP | URL |\n| --- | --- |\n" + linha + linha,
                      "## Catálogo\n| x | https://a.org/mcp | não | — | * | — |\n"):
            with open(ruim, "w", encoding="utf-8") as f:
                f.write(texto)
            with self.assertRaises(mcp.Erro):
                mcp.ler_catalogo(ruim)


if __name__ == "__main__":
    unittest.main()
