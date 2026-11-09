import copy
import json
import os
import tempfile
import unittest

import apoio  # noqa: F401  (ajusta o sys.path)
import plano


def _ler(arq):
    with open(arq, encoding="utf-8") as f:
        return json.load(f)


BASE = {
    "demanda": "d",
    "tarefas": [
        {"id": "T1", "titulo": "a", "criterios": ["CA-1"], "estado": "feito"},
        {"id": "T2", "titulo": "b", "criterios": ["CA-1"], "depende_de": ["T1"], "estado": "a_fazer"},
        {"id": "T3", "titulo": "c", "criterios": ["CA-2"], "depende_de": ["T2"], "estado": "a_fazer"},
        {"id": "T4", "titulo": "d", "criterios": ["CA-3"], "estado": "a_fazer"},
        {"id": "T5", "titulo": "e", "criterios": ["CA-3"], "estado": "a_fazer", "protegida": True},
    ],
}


class PlanoTests(unittest.TestCase):
    def setUp(self):
        self.dados = copy.deepcopy(BASE)

    def test_prontas_respeita_dependencias_e_protegidas(self):
        self.assertEqual([t["id"] for t in plano.prontas(self.dados)], ["T2", "T4"])

    def test_validar_aceita_plano_bom(self):
        self.assertEqual(plano.validar(self.dados), [])

    def test_validar_aponta_problemas(self):
        self.dados["tarefas"].append({"id": "T2", "titulo": "", "estado": "x", "depende_de": ["T9"]})
        erros = "\n".join(plano.validar(self.dados))
        for trecho in ("id repetido", "sem título", "estado 'x'", "'T9'", "sem critérios"):
            self.assertIn(trecho, erros)

    def test_validar_detecta_ciclo(self):
        self.dados["tarefas"][1]["depende_de"] = ["T3"]
        self.assertTrue(any("circular" in e for e in plano.validar(self.dados)))

    def test_marcar_grava_commit_e_wi_e_recusa_protegida(self):
        t = plano.marcar(self.dados, "T2", "feito", commit="abc1234", wi="1004", nota="ok")
        self.assertEqual((t["estado"], t["commit"], t["wi"], t["notas"]), ("feito", "abc1234", 1004, ["ok"]))
        self.assertEqual([x["id"] for x in plano.prontas(self.dados)], ["T3", "T4"])
        with self.assertRaises(ValueError):
            plano.marcar(self.dados, "T5", "feito")
        with self.assertRaises(ValueError):
            plano.marcar(self.dados, "T2", "pronto")

    def test_motivo_quando_nao_ha_proxima(self):
        for t in self.dados["tarefas"]:
            if not t.get("protegida"):
                t["estado"] = "feito"
        self.assertEqual(plano.motivo_sem_proxima(self.dados), "fila concluída")

    def test_cli_marcar_persiste(self):
        with tempfile.TemporaryDirectory() as d:
            arq = os.path.join(d, "tarefas.json")
            plano.salvar(arq, self.dados)
            self.assertEqual(plano.main(["plano.py", "marcar", arq, "T4", "andamento"]), 0)
            self.assertEqual(_ler(arq)["tarefas"][3]["estado"], "andamento")
            self.assertEqual(plano.main(["plano.py", "proxima", arq]), 0)

    def test_tabela_markdown(self):
        tabela = plano.tabela(self.dados)
        self.assertIn("| T2 | b |  | T1 | a_fazer | — | — |", tabela)
        self.assertIn("(protegida)", tabela)

    def test_modelo_do_plugin_e_valido(self):
        modelo = _ler(os.path.join(apoio.FLUXO, "templates", "tarefas.json"))
        self.assertEqual(plano.validar(modelo), [])


if __name__ == "__main__":
    unittest.main()
