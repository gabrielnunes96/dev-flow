import json
import os
import unittest

from apoio import FLUXO, RAIZ_REPO, ProjetoTemporario

import perfil


def _ler(arq):
    with open(arq, encoding="utf-8") as f:
        return json.load(f)


class PerfilTests(unittest.TestCase):
    def test_encontra_raiz_subindo_diretorios(self):
        with ProjetoTemporario({"nome": "X", "stacks": ["sql"]}) as raiz:
            sub = os.path.join(raiz, "a", "b")
            os.makedirs(sub)
            self.assertEqual(os.path.normcase(perfil.encontrar_raiz(sub)), os.path.normcase(raiz))
            self.assertEqual(perfil.carregar(sub)[1]["nome"], "X")

    def test_sem_perfil(self):
        with ProjetoTemporario() as raiz:
            self.assertEqual(perfil.carregar(raiz), (None, {}))

    def test_json_invalido(self):
        with ProjetoTemporario({"nome": "X"}) as raiz:
            with open(os.path.join(raiz, ".claude", "projeto.json"), "w") as f:
                f.write("{nome:")
            with self.assertRaises(ValueError):
                perfil.carregar(raiz)

    def test_validar_erros_e_avisos(self):
        problemas = perfil.validar(
            {
                "stacks": ["cobol"],
                "rastreador": {"tipo": "azure-boards"},
                "validacao": {"tipo": "http"},
                "git": {"push": "sempre"},
                "protecao": {"gerados": [{"regex": "("}]},
            }
        )
        erros = [m for n, m in problemas if n == "erro"]
        avisos = [m for n, m in problemas if n == "aviso"]
        for trecho in ("nome", "rastreador.org", "rastreador.projeto", "base_url", "git.push", "gerados[0].regex"):
            self.assertTrue(any(trecho in e for e in erros), trecho)
        self.assertTrue(any("cobol" in a for a in avisos))
        self.assertTrue(any("comandos.teste" in a for a in avisos))

    def test_validar_secao_design(self):
        ok = perfil.validar({"nome": "x", "stacks": ["front"], "comandos": {"teste": "t"},
                             "design": {"tokens": "src/tokens.css", "plataformas": ["web", "ios"]}})
        self.assertEqual([m for n, m in ok if n == "erro"], [])
        erros = [m for n, m in perfil.validar({"nome": "x", "stacks": ["front"], "design": {"tokens": 1, "plataformas": ["tv"]}}) if n == "erro"]
        self.assertTrue(any("design.tokens" in e for e in erros))
        self.assertTrue(any("'tv'" in e for e in erros))
        erros = [m for n, m in perfil.validar({"nome": "x", "stacks": ["front"], "design": []}) if n == "erro"]
        self.assertTrue(any(e.startswith("design:") for e in erros))

    def test_obter_campo_aninhado(self):
        p = {"git": {"push": "humano"}}
        self.assertEqual(perfil.obter(p, "git.push"), "humano")
        self.assertIsNone(perfil.obter(p, "git.base"))
        self.assertEqual(perfil.obter(p, "x.y", 1), 1)

    def test_modelos_e_exemplos_sao_validos(self):
        arquivos = [os.path.join(FLUXO, "templates", "projeto.json")]
        exemplos = os.path.join(RAIZ_REPO, "exemplos")
        for raiz, _, nomes in os.walk(exemplos):
            arquivos += [os.path.join(raiz, n) for n in nomes if n == "projeto.json"]
        for arq in arquivos:
            dados = _ler(arq)
            erros = [m for n, m in perfil.validar(dados) if n == "erro"]
            self.assertEqual(erros, [], arq)


if __name__ == "__main__":
    unittest.main()
