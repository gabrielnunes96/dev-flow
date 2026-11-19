"""Suíte de comportamento dos especialistas: estrutura dos casos e executor host-agnóstico (scripts/avaliar_agentes.py)."""
import contextlib
import io
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

from apoio import RAIZ_REPO

sys.path.insert(0, os.path.join(RAIZ_REPO, "scripts"))
import avaliar_agentes as av  # noqa: E402

# Campos aceitos pelo `claude plugin eval` (chave desconhecida é erro lá).
CAMPOS_PROMPT = {"name", "description", "tags", "plugins", "runs", "expected_outcome", "model", "max_turns",
                 "timeout_seconds", "allowed_tools", "append_system_prompt", "env"}
TIPOS = {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"}


def _main(*args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return av.main(list(args))


def _cmd(codigo):
    args = (sys.executable, "-c", codigo)
    return subprocess.list2cmdline(args) if os.name == "nt" else " ".join(shlex.quote(a) for a in args)


AGENTE_FALSO = _cmd("import sys; d=sys.stdin.read(); print('achado: forEach async sem await' if 'forEach' in d else 'nada')")
JUIZ_APROVA = _cmd("import sys; sys.stdin.read(); print('PASS')")
JUIZ_MARKDOWN = _cmd("import sys; sys.stdin.read(); print('Analisei a resposta.'); print('Veredito: **PASS**')")
JUIZ_REPROVA = _cmd("import sys; sys.stdin.read(); print('FAIL porque sim')")


class EstruturaDosCasosTests(unittest.TestCase):
    def test_casos_validos_para_o_claude_plugin_eval_e_para_o_executor(self):  # CA-9
        lista = av.casos()
        self.assertGreaterEqual(len(lista), 5)
        agentes = {c["agente"] for c in lista}
        self.assertTrue({"revisor", "seguranca", "arquiteto", "testador"} <= agentes)
        for c in lista:
            self.assertTrue(os.path.isfile(c["arquivo_agente"]), c["nome"])
            self.assertLessEqual(set(c["campos"]), CAMPOS_PROMPT, c["nome"])
            self.assertGreater(len(c["prompt"]), 80, c["nome"])
            self.assertTrue(c["graders"], c["nome"])
            for g in c["graders"]:
                tipo = g["campos"].get("type")
                self.assertIn(tipo, TIPOS, f"{c['nome']}/{g['nome']}")
                self.assertNotEqual(tipo, "tool_used", "tool_used depende do host; use regex ou llm")
                if tipo == "regex":
                    re.compile(g["campos"]["pattern"])
                    self.assertNotIn("(?", g["campos"]["pattern"], "flags inline não valem no claude plugin eval")
                for chave, valor in g["campos"].items():
                    self.assertFalse(str(valor) in ("|", ">", "|-", ">-"), "escalar em bloco: os dois executores leem diferente")
                if tipo == "regex":
                    with open(os.path.join(c["pasta"], "graders", g["nome"] + ".md"), encoding="utf-8") as f:
                        self.assertNotIn('pattern: "', f.read(), "pattern entre aspas simples (escape igual nos dois executores)")
                    if g["campos"].get("match", "contains") == "contains":
                        flags = re.I if "i" in str(g["campos"].get("flags", "")) else 0
                        self.assertIsNone(re.search(g["campos"]["pattern"], c["prompt"], flags),
                                          f"{c['nome']}/{g['nome']}: o padrão casa com o próprio prompt e aprovaria qualquer eco")
                if tipo == "llm":
                    self.assertIn("PASS", g["criterio"])
                    self.assertIn("FAIL", g["criterio"])

    def test_resultados_ignorados_pelo_git(self):
        with open(os.path.join(RAIZ_REPO, ".gitignore"), encoding="utf-8") as f:
            self.assertIn("evals/results/", f.read())


class ExecutorTests(unittest.TestCase):  # CA-11
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="avaliar-")
        self._orig = (av.RAIZ, av.PLUGINS)
        av.RAIZ, av.PLUGINS = self.dir, os.path.join(self.dir, "plugins")
        base = os.path.join(av.PLUGINS, "p")
        self._escrever(os.path.join(base, "agents", "revisor.md"), "---\nname: revisor\n---\nVocê revisa código.\n")
        caso = os.path.join(base, "evals", "revisor", "await")
        self._escrever(os.path.join(caso, "prompt.md"), "---\nname: x\ntimeout_seconds: 60\n---\nRevise: itens.forEach(async i => salvar(i))\n")
        self._escrever(os.path.join(caso, "graders", "a.md"), "---\ntype: regex\npattern: 'forEach'\nflags: i\nmatch: contains\n---\n")
        self._escrever(os.path.join(caso, "graders", "b.md"), "---\ntype: regex\npattern: 'nada'\nmatch: not_contains\n---\n")
        self._escrever(os.path.join(caso, "graders", "c.md"), "---\ntype: llm\n---\nPASS se apontar o defeito.\nFAIL se não.\n")
        self._escrever(os.path.join(caso, "graders", "d.md"), "---\ntype: tool_used\ntool: Agent\n---\n")
        outro = os.path.join(base, "evals", "revisor", "limpo")
        self._escrever(os.path.join(outro, "prompt.md"), "---\nname: y\n---\nRevise: const a = 1\n")
        self._escrever(os.path.join(outro, "graders", "a.md"), "---\ntype: regex\npattern: 'forEach'\nmatch: contains\n---\n")

    def tearDown(self):
        av.RAIZ, av.PLUGINS = self._orig
        shutil.rmtree(self.dir, ignore_errors=True)

    def _escrever(self, arq, texto):
        os.makedirs(os.path.dirname(arq), exist_ok=True)
        with open(arq, "w", encoding="utf-8") as f:
            f.write(texto)

    def _rodar(self, filtro, juiz=None):
        return av.rodar(av.casos(filtro=filtro), AGENTE_FALSO, juiz, saida=lambda _: None)

    def test_aprova_caso_cuja_resposta_passa_nas_verificacoes(self):
        (r,), falhou = self._rodar("revisor/await")
        self.assertFalse(falhou)
        self.assertEqual(r["situacao"], "OK")
        notas = r["verificacoes"][0]
        self.assertEqual((notas["a"], notas["b"], notas["c"], notas["d"]), (True, True, None, None))

    def test_reprova_caso_que_falha_e_sai_com_1(self):
        (r,), falhou = self._rodar("revisor/limpo")
        self.assertTrue(falhou)
        self.assertEqual(r["situacao"], "REPROVADO")
        self.assertEqual(_main(*["--comando", AGENTE_FALSO, "--caso", "revisor/limpo"]), 1)
        self.assertEqual(_main(*["--comando", AGENTE_FALSO, "--caso", "revisor/await"]), 0)

    def test_juiz_decide_verificacao_llm(self):
        (r,), _ = self._rodar("revisor/await", JUIZ_APROVA)
        self.assertTrue(r["verificacoes"][0]["c"])
        (r,), _ = self._rodar("revisor/await", JUIZ_MARKDOWN)
        self.assertTrue(r["verificacoes"][0]["c"])
        (r,), falhou = self._rodar("revisor/await", JUIZ_REPROVA)
        self.assertTrue(falhou)
        self.assertFalse(r["verificacoes"][0]["c"])

    def test_prompt_leva_o_especialista_e_pode_ir_por_arquivo(self):
        prompt = av.montar_prompt(av.casos(filtro="revisor/await")[0])
        self.assertIn("Você revisa código.", prompt)
        self.assertNotIn("name: revisor", prompt)
        cmd = _cmd("import sys; print(open(sys.argv[1], encoding='utf-8').read())") + " {prompt_arquivo}"
        self.assertIn("forEach", av.executar(cmd, prompt, 30))

    def test_erro_de_comando_e_especialista_inexistente(self):
        (r,), falhou = av.rodar(av.casos(filtro="revisor/await"), "comando-que-nao-existe-xyz", saida=lambda _: None)
        self.assertTrue(falhou)
        self.assertEqual(r["situacao"], "ERRO")
        with self.assertRaisesRegex(av.Erro, "Not logged in"):
            av.executar(_cmd("print('Not logged in'); raise SystemExit(1)"), "x", 30)
        os.remove(os.path.join(av.PLUGINS, "p", "agents", "revisor.md"))
        with self.assertRaises(av.Erro):
            av.montar_prompt(av.casos(filtro="revisor/await")[0])

    def test_caso_sem_verificacao_avaliada_reprova(self):
        caso = os.path.join(av.PLUGINS, "p", "evals", "revisor", "so-llm")
        self._escrever(os.path.join(caso, "prompt.md"), "---\nname: z\n---\nRevise algo.\n")
        self._escrever(os.path.join(caso, "graders", "a.md"), "---\ntype: llm\n---\nPASS se ok.\nFAIL se não.\n")
        (r,), falhou = self._rodar("revisor/so-llm")
        self.assertEqual(r["situacao"], "NÃO AVALIADO")
        self.assertTrue(falhou)

    def test_roda_em_pasta_temporaria_e_grader_mal_formado_vira_erro(self):
        saida = av.executar(_cmd("import os, sys; sys.stdin.read(); print(os.getcwd())"), "x", 30).strip()
        self.assertNotEqual(os.path.realpath(saida), os.path.realpath(os.getcwd()))
        self.assertFalse(os.path.exists(saida))
        self._escrever(os.path.join(av.PLUGINS, "p", "evals", "revisor", "await", "graders", "e.md"), "---\ntype: regex\n---\n")
        (r,), falhou = self._rodar("revisor/await")
        self.assertEqual(r["situacao"], "ERRO")
        self.assertIn("mal formada", r["erro"])

    def test_listar(self):
        self.assertEqual(_main(*["--listar"]), 0)
        self.assertEqual(_main(*["--listar", "--caso", "ninguem/*"]), 1)


if __name__ == "__main__":
    unittest.main()
