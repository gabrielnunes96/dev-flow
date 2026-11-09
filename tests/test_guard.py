import json
import os
import subprocess
import sys
import unittest

from apoio import FLUXO, RAIZ_REPO, ProjetoTemporario

import guard

PERFIL = {
    "nome": "Teste",
    "stacks": ["dotnet"],
    "protecao": {
        "textos_proibidos": [{"regex": r"(?<![\w.])5-Projeto\.Excluido", "motivo": "diretório excluído"}],
        "diretorios_proibidos": ["../5-Excluido"],
        "gerados": [{"regex": r"[\\/]Sdk[\\/](Api|Model)[\\/]", "excecoes": ["ApiClient.Custom.cs"], "motivo": "SDK gerado"}],
        "segredos": {"arquivos": [".claude/local/token.txt"], "scripts_permitidos": r"(token_login|http_lote)\.py"},
    },
}

# Montado em tempo de execução: o literal faria o próprio guard barrar commits que mexam nesta linha.
JWT = ".".join(["eyJ" + "hbGciOiJIUzI1NiJ9a", "eyJ" + "zdWIiOiIxMjM0NTY3ODkwIn0b", "SflKxwRJSMeKKF2QT4fwpMeJf36"])


def chamada(ferramenta, **entrada):
    return {"tool_name": ferramenta, "tool_input": entrada}


class GuardTests(unittest.TestCase):
    def bloqueia(self, dados, raiz, perfil=PERFIL, diff=""):
        with self.assertRaises(guard.Bloqueio) as ctx:
            guard.verificar(dados, raiz, perfil, obter_diff=lambda _: diff)
        return str(ctx.exception)

    def libera(self, dados, raiz, perfil=PERFIL, diff=""):
        guard.verificar(dados, raiz, perfil, obter_diff=lambda _: diff)

    def test_texto_proibido_bloqueia_mas_nome_parecido_passa(self):
        with ProjetoTemporario(PERFIL) as raiz:
            self.assertIn("excluído", self.bloqueia(chamada("Bash", command="ls ../5-Projeto.Excluido"), raiz))
            self.libera(chamada("Bash", command="ls ../5.1-Projeto.Excluido"), raiz)

    def test_diretorio_proibido_em_leitura_e_busca_acima(self):
        with ProjetoTemporario(PERFIL) as raiz:
            self.bloqueia(chamada("Read", file_path=os.path.join(raiz, "..", "5-Excluido", "a.cs")), raiz)
            self.bloqueia(chamada("Grep", pattern="x", path=os.path.dirname(raiz)), raiz)
            self.libera(chamada("Grep", pattern="x", path=raiz), raiz)
            self.libera(chamada("Read", file_path=os.path.join(raiz, "src", "a.cs")), raiz)

    def test_gerado_bloqueia_edicao_com_excecao(self):
        with ProjetoTemporario(PERFIL) as raiz:
            self.bloqueia(chamada("Edit", file_path=os.path.join(raiz, "Sdk", "Api", "X.cs")), raiz)
            self.libera(chamada("Edit", file_path=os.path.join(raiz, "Sdk", "Api", "ApiClient.Custom.cs")), raiz)
            self.libera(chamada("Read", file_path=os.path.join(raiz, "Sdk", "Api", "X.cs")), raiz)

    def test_segredo_nao_e_lido_pelo_chat(self):
        with ProjetoTemporario(PERFIL) as raiz:
            self.bloqueia(chamada("Read", file_path=os.path.join(raiz, ".claude", "local", "token.txt")), raiz)
            self.bloqueia(chamada("Bash", command="cat .claude/local/token.txt"), raiz)
            self.libera(chamada("Bash", command="python -I scripts/token_login.py # grava token.txt"), raiz)

    def test_segredo_casa_o_nome_inteiro_nao_substring(self):
        perfil = {"nome": "T", "stacks": ["node"], "protecao": {"segredos": {"arquivos": ["server/.env", "deploy/.env"]}}}
        with ProjetoTemporario(perfil) as raiz:
            self.bloqueia(chamada("Bash", command="cat server/.env"), raiz, perfil)
            self.bloqueia(chamada("Bash", command="cp exemplo.env .env && cat .env"), raiz, perfil)
            self.bloqueia(chamada("Bash", command="grep X '.env'"), raiz, perfil)
            self.libera(chamada("Bash", command="grep -n process.env.PORTA src/config.ts"), raiz, perfil)
            self.libera(chamada("Bash", command="cat deploy/exemplo.env"), raiz, perfil)
            self.libera(chamada("Bash", command="ls .env.example"), raiz, perfil)

    def test_push_bloqueado_so_quando_e_comando(self):
        with ProjetoTemporario(PERFIL) as raiz:
            self.bloqueia(chamada("Bash", command="git status && git push origin main"), raiz)
            self.bloqueia(chamada("PowerShell", command="git -C . push"), raiz)
            self.libera(chamada("Bash", command='echo "nunca rode git push aqui"'), raiz)
            self.libera(chamada("Bash", command="git push"), raiz, perfil={**PERFIL, "git": {"push": "permitido"}})

    def test_commit_com_segredo_no_diff(self):
        with ProjetoTemporario(PERFIL) as raiz:
            self.assertIn("JWT", self.bloqueia(chamada("Bash", command='git commit -m "x"'), raiz, diff="+token = " + JWT))
            self.bloqueia(chamada("Bash", command="git commit -m x"), raiz, diff="+-----BEGIN RSA PRIVATE KEY-----")
            self.libera(chamada("Bash", command="git commit -m x"), raiz, diff="+var x = 1;")

    def test_sem_perfil_so_checa_segredo_no_commit(self):
        with ProjetoTemporario() as raiz:
            self.libera(chamada("Bash", command="git push"), raiz, perfil={})
            self.bloqueia(chamada("Bash", command="git commit -m x"), raiz, perfil={}, diff="+" + JWT)


class HookProcessoTests(unittest.TestCase):
    """O hook como o Claude Code o chama: JSON no stdin, código 2 e motivo no stderr quando bloqueia."""

    def rodar(self, dados):
        return subprocess.run(
            [sys.executable, "-I", os.path.join(FLUXO, "hooks", "guard.py")],
            input=json.dumps(dados), capture_output=True, text=True, encoding="utf-8",
        )

    def test_bloqueia_com_codigo_2_e_libera_com_0(self):
        with ProjetoTemporario(PERFIL) as raiz:
            r = self.rodar({**chamada("Bash", command="git push"), "cwd": raiz})
            self.assertEqual(r.returncode, 2)
            self.assertIn("git push", r.stderr)
            self.assertEqual(self.rodar({**chamada("Bash", command="git status"), "cwd": raiz}).returncode, 0)

    def test_perfil_invalido_nao_bloqueia(self):
        with ProjetoTemporario({"nome": "X"}) as raiz:
            with open(os.path.join(raiz, ".claude", "projeto.json"), "w") as f:
                f.write("{")
            r = self.rodar({**chamada("Bash", command="git push"), "cwd": raiz})
            self.assertEqual(r.returncode, 0)
            self.assertIn("inválido", r.stderr)


class PerfilPonteTests(unittest.TestCase):
    """O guard genérico com exemplos/ponte/projeto.json bloqueia o mesmo que o guard.py original da Ponte."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(RAIZ_REPO, "exemplos", "ponte", "projeto.json"), encoding="utf-8") as f:
            cls.perfil = json.load(f)
        cls.excluido = "5" + "-Acme.API.Ponte"  # montado em tempo de execução: o nome literal é bloqueado no editor

    def bloqueado(self, dados, raiz):
        try:
            guard.verificar(dados, raiz, self.perfil, obter_diff=lambda _: "")
            return False
        except guard.Bloqueio:
            return True

    def test_equivalente_ao_guard_original(self):
        with ProjetoTemporario(self.perfil) as raiz:
            pai = os.path.dirname(raiz)
            casos = [
                (chamada("Read", file_path=os.path.join(pai, self.excluido, "x.cs")), True),
                (chamada("Bash", command=f"ls ../{self.excluido}"), True),
                (chamada("Grep", pattern="x", path=pai), True),
                (chamada("Grep", pattern="x", path=raiz), False),
                (chamada("Edit", file_path=os.path.join(raiz, "4-infrastructure", "Master", "Acme.ProvedorAExtended", "Api", "ClaimsApi.cs")), True),
                (chamada("Edit", file_path=os.path.join(raiz, "4-infrastructure", "Master", "Acme.ProvedorA", "Client", "ApiClient.cs")), True),
                (chamada("Edit", file_path=os.path.join(raiz, "4-infrastructure", "Master", "Acme.ProvedorAExtended", "Client", "ApiClient.Custom.cs")), False),
                (chamada("Edit", file_path=os.path.join(raiz, "3-core", "Acme.Ponte.Service", "X.cs")), False),
                (chamada("Read", file_path=os.path.join(raiz, ".claude", "local", "token" + ".txt")), True),
                (chamada("Bash", command="python -I .claude/skills/proxima-task/scripts/chamar.py < lote.json"), False),
                (chamada("Bash", command="git push"), True),
                (chamada("Bash", command="git log --oneline master..HEAD"), False),
            ]
            for dados, esperado in casos:
                with self.subTest(dados=dados):
                    self.assertEqual(self.bloqueado(dados, raiz), esperado)


if __name__ == "__main__":
    unittest.main()
