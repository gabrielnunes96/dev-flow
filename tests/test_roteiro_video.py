import copy
import json
import os
import sys
import tempfile
import unittest
import wave

import apoio

sys.path.insert(0, os.path.join(apoio.RAIZ_REPO, "plugins", "video", "scripts"))
import roteiro  # noqa: E402

EXEMPLO = os.path.join(apoio.RAIZ_REPO, "exemplos", "video", "migracao-ponte.json")

BASE = {
    "cenas": [
        {"id": "abertura", "tipo": "abertura", "fala": "Olá, este é o resumo.", "titulo": "Resumo"},
        {"id": "lista", "tipo": "lista", "capitulo": "Mudanças", "titulo": "O que mudou",
         "fala": "Primeiro, as rotas. Depois, os testes.",
         "itens": [{"titulo": "Rotas", "quando": "as rotas"}, {"titulo": "Testes", "quando": ["os testes", 0.5]}]},
        {"id": "fim", "tipo": "encerramento", "fala": "Fim.", "linhas": [{"texto": "Fim.", "quando": "Fim"}]},
    ]
}


class RoteiroVideoTests(unittest.TestCase):
    def setUp(self):
        self.r = copy.deepcopy(BASE)

    def test_exemplo_do_marketplace_e_valido(self):
        self.assertEqual(roteiro.validar(roteiro.carregar(EXEMPLO)), [])

    def test_aceita_roteiro_bom(self):
        self.assertEqual(roteiro.validar(self.r), [])

    def test_quando_fora_da_fala(self):
        self.r["cenas"][1]["itens"][0]["quando"] = "palavra ausente"
        self.assertIn("lista: quando 'palavra ausente' não aparece na fala", roteiro.validar(self.r))

    def test_tipo_desconhecido_id_repetido_e_campo_faltando(self):
        self.r["cenas"][0]["tipo"] = "carrossel"
        self.r["cenas"][2]["id"] = "lista"
        del self.r["cenas"][1]["titulo"]
        erros = "\n".join(roteiro.validar(self.r))
        self.assertIn("tipo desconhecido 'carrossel'", erros)
        self.assertIn("lista: id repetido", erros)
        self.assertIn("lista: falta 'titulo'", erros)

    def test_limite_de_itens(self):
        self.r["cenas"][1]["itens"] = [{"titulo": str(i)} for i in range(6)]
        self.assertIn("lista: 'itens' tem 6 itens (máximo 5)", roteiro.validar(self.r))

    def test_antes_depois_exige_camadas_validas(self):
        self.r["cenas"].insert(1, {"id": "ad", "tipo": "antes_depois", "titulo": "t", "fala": "x",
                                   "antes": {"camadas": []}, "agora": {"camadas": [[{"titulo": "a"}] * 4]}})
        erros = "\n".join(roteiro.validar(self.r))
        self.assertIn("'antes.camadas'", erros)
        self.assertIn("'agora.camadas'", erros)

    def test_linha_do_tempo_e_instante_da_palavra(self):
        total = roteiro.linha_do_tempo(self.r, {"abertura": 2.0, "lista": 4.0, "fim": 1.0})
        a, l, f = self.r["cenas"]
        self.assertAlmostEqual(a["lead"], roteiro.LEAD + 0.6)
        self.assertAlmostEqual(l["ini"], a["dur"])
        self.assertAlmostEqual(f["dur"], roteiro.LEAD + 1.0 + roteiro.TAIL + 2.2)
        self.assertAlmostEqual(total, a["dur"] + l["dur"] + f["dur"])
        fala = l["fala"]
        esperado = l["lead"] + 4.0 * fala.find("os testes") / len(fala) + 0.5
        self.assertAlmostEqual(roteiro.at(l, ["os testes", 0.5]), esperado)
        self.assertEqual(roteiro.at(l, None, 3.0), 3.0)
        self.assertEqual(roteiro.at(l, 1.5), 1.5)

    def test_duracoes_da_pasta(self):
        with tempfile.TemporaryDirectory() as pasta:
            for c, seg in (("abertura", 1.0), ("lista", 0.5), ("fim", 0.25)):
                with wave.open(os.path.join(pasta, f"voz_{c}.wav"), "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(44100)
                    w.writeframes(b"\x00\x00" * int(44100 * seg))
            self.assertEqual(roteiro.duracoes_da_pasta(self.r, pasta), {"abertura": 1.0, "lista": 0.5, "fim": 0.25})


if __name__ == "__main__":
    unittest.main()
