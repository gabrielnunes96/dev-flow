"""Conhecimento atualizável: scripts/atualizar_conhecimento.py e a estrutura dos atual.md das stacks."""
import contextlib
import datetime as dt
import http.client
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from apoio import RAIZ_REPO

sys.path.insert(0, os.path.join(RAIZ_REPO, "scripts"))
import atualizar_conhecimento as ac  # noqa: E402

HOJE = dt.date(2026, 11, 19)

ATUAL = """# Conhecimento atual: {nome}
<!-- dev-flow:conhecimento revisado_em={revisado} produtos={produtos} -->

## Fontes oficiais
- https://exemplo.org/releases

## Versões
<!-- versoes:inicio -->
{bloco}
<!-- versoes:fim -->

## Mudanças a observar
- nada
"""

BLOCO_NODE = """| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |
| --- | --- | --- | --- | --- | --- | --- |
| nodejs | 26 | suportado | 2026-05-05 | 2027-10-27 | 2029-04-30 | 26.1.0 |
| nodejs | 25 | suportado | 2025-10-15 | 2026-04-01 | 2026-06-01 | 25.9.0 |
| nodejs | 24 | LTS | 2025-05-06 | 2026-10-20 | 2028-04-30 | 24.22.3 |"""

NODEJS = [
    {"cycle": "27", "releaseDate": "2026-11-01", "lts": False, "eol": "2027-06-01", "latest": "27.0.0", "support": "2027-04-01"},
    {"cycle": "26", "releaseDate": "2026-05-05", "lts": "2026-10-28", "eol": "2029-04-30", "latest": "26.13.1", "support": "2027-10-27"},
    {"cycle": "25", "releaseDate": "2025-10-15", "lts": False, "eol": "2026-06-01", "latest": "25.9.0", "support": "2026-04-01"},
    {"cycle": "24", "releaseDate": "2025-05-06", "lts": "2025-10-28", "eol": "2028-04-30", "latest": "24.22.3", "support": "2026-10-20"},
]


class ConhecimentoScriptTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="conhecimento-")
        self.plugins = os.path.join(self.dir, "plugins")
        self.fonte = os.path.join(self.dir, "fonte")
        os.makedirs(self.fonte)
        with open(os.path.join(self.fonte, "nodejs.json"), "w", encoding="utf-8") as f:
            json.dump(NODEJS, f)
        self._orig = (ac.RAIZ, ac.PLUGINS)
        ac.RAIZ, ac.PLUGINS = self.dir, self.plugins
        self.node = self._atual("node", "nodejs", BLOCO_NODE)
        self.py = self._atual("python", "python", "")
        self._escrever(os.path.join(self.plugins, "stack-node", "skills", "node", "SKILL.md"),
                       "# Node\n\nUse Node 24 ou Node 26.\nImagem: node:25-alpine\nArmadilha antes do Node 25 e desde o Node 23.\n")

    def tearDown(self):
        ac.RAIZ, ac.PLUGINS = self._orig
        shutil.rmtree(self.dir, ignore_errors=True)

    def _escrever(self, arq, texto):
        os.makedirs(os.path.dirname(arq), exist_ok=True)
        with open(arq, "w", encoding="utf-8") as f:
            f.write(texto)

    def _atual(self, stack, produtos, bloco, revisado="2026-11-01"):
        arq = os.path.join(self.plugins, f"stack-{stack}", "referencias", "atual.md")
        self._escrever(arq, ATUAL.format(nome=stack, revisado=revisado, produtos=produtos, bloco=bloco))
        return arq

    def _ler(self, arq):
        with open(arq, encoding="utf-8") as f:
            return f.read()

    def test_detecta_ciclo_novo_fim_de_suporte_e_lts_e_regenera(self):  # CA-4
        achados = ac.levantar(HOJE, stacks=["node"], fonte_dir=self.fonte)
        tipos = {(t, m) for t, m in achados}
        self.assertIn(("novo_ciclo", "stack-node: nodejs 27 (suportado)"), tipos)
        self.assertTrue(any(t == "fim_de_suporte" and "nodejs 25" in m for t, m in achados))
        self.assertTrue(any(t == "novo_lts" and "nodejs 26" in m for t, m in achados))
        linhas = ac.linhas_da_tabela(ac.BLOCO.search(self._ler(self.node)).group(2))
        self.assertEqual(linhas[("nodejs", "27")], "suportado")
        self.assertEqual(linhas[("nodejs", "26")], "LTS")
        self.assertEqual(linhas[("nodejs", "25")], "sem suporte")

    def test_aponta_versao_sem_suporte_citada_com_linha(self):  # CA-5
        achados = ac.levantar(HOJE, stacks=["node"], fonte_dir=self.fonte, gravar=False)
        citadas = [m for t, m in achados if t == "versao_sem_suporte"]
        self.assertEqual(citadas, [os.path.join("plugins", "stack-node", "skills", "node", "SKILL.md") + ":4 cita nodejs 25, sem suporte"])

    def test_falha_de_fonte_nao_altera_o_arquivo_e_segue(self):  # CA-6
        antes = self._ler(self.py)
        achados = ac.levantar(HOJE, fonte_dir=self.fonte)
        self.assertTrue(any(t == "falha_fonte" and "stack-python" in m for t, m in achados))
        self.assertEqual(self._ler(self.py), antes)
        self.assertIn("| nodejs | 27 |", self._ler(self.node))

    def test_sem_mudanca_nao_regrava(self):
        ac.levantar(HOJE, stacks=["node"], fonte_dir=self.fonte)
        depois = self._ler(self.node)
        achados = ac.levantar(HOJE + dt.timedelta(days=1), stacks=["node"], fonte_dir=self.fonte)
        self.assertEqual(self._ler(self.node), depois)
        self.assertEqual([t for t, _ in achados], ["versao_sem_suporte"])

    def test_primeira_geracao_nao_gera_achado_de_ciclo(self):
        self._atual("node", "nodejs", "")
        achados = ac.levantar(HOJE, stacks=["node"], fonte_dir=self.fonte, gravar=False)
        self.assertFalse([t for t, _ in achados if t in ("novo_ciclo", "fim_de_suporte", "novo_lts")])

    def test_verificar_aponta_revisao_vencida_e_estrutura(self):  # CA-7
        self.assertEqual(ac.verificar(HOJE), [])
        self._atual("python", "python", "", revisado="2026-01-01")
        problemas = ac.verificar(HOJE, max_dias=120)
        self.assertEqual(len(problemas), 1)
        self.assertIn("revisão vencida", problemas[0])
        os.makedirs(os.path.join(self.plugins, "stack-go"))
        self.assertTrue(any("stack-go: falta referencias/atual.md" in p for p in ac.verificar(HOJE)))
        self._escrever(self.py, "# sem nada\n")
        self.assertGreaterEqual(len([p for p in ac.verificar(HOJE) if "stack-python" in p]), 4)

    def _main(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return ac.main(list(args))

    def _fonte(self, produto, dados):
        with open(os.path.join(self.fonte, f"{produto}.json"), "w", encoding="utf-8") as f:
            f.write(dados if isinstance(dados, str) else json.dumps(dados))

    def test_suporte_ativo_encerrado_sem_fim_de_vida(self):
        self.assertEqual(ac.situacao({"cycle": "17", "eol": False, "support": "2024-04-25"}, HOJE), "suporte ativo encerrado")
        self.assertEqual(ac.situacao({"cycle": "19", "eol": False, "support": True}, HOJE), "suportado")
        self.assertEqual(ac.situacao({"cycle": "22", "lts": "2024-10-29", "eol": "2027-04-30", "support": "2025-10-21"}, HOJE), "LTS")
        NODEJS_NOVO = [dict(c) for c in NODEJS]
        NODEJS_NOVO[0]["support"] = "2026-11-01"
        self._fonte("nodejs", NODEJS_NOVO)
        ac.levantar(HOJE - dt.timedelta(days=30), stacks=["node"], fonte_dir=self.fonte)
        achados = ac.levantar(HOJE, stacks=["node"], fonte_dir=self.fonte)
        self.assertTrue(any(t == "fim_de_suporte" and "nodejs 27 encerrou o suporte ativo" in m for t, m in achados))

    def test_ciclo_sem_ponto_zero_e_ano_do_sql_server(self):  # CA-5 (.NET e SQL Server)
        self._fonte("dotnet", [{"cycle": "10", "lts": True, "eol": "2028-11-14"}, {"cycle": "8", "lts": True, "eol": "2026-11-10"}])
        self._fonte("mssqlserver", [{"cycle": "16.0", "releaseLabel": "2022", "eol": "2033-01-11"},
                                    {"cycle": "12.0-sp3", "releaseLabel": "2014 'X' SP3", "eol": "2024-07-09"}])
        self._atual("dotnet", "dotnet", "")
        self._atual("sql", "mssqlserver", "")
        self._escrever(os.path.join(self.plugins, "stack-dotnet", "templates", "Dockerfile"),
                       "ARG DOTNET=8.0\nFROM mcr.microsoft.com/dotnet/aspnet:10.0\nVer .NET 8 e SQL Server 2014; SQL Server 2022 ok\n")
        citadas = [m for t, m in ac.levantar(HOJE, stacks=["dotnet", "sql"], fonte_dir=self.fonte, gravar=False)
                   if t == "versao_sem_suporte"]
        self.assertEqual(len(citadas), 3, citadas)
        self.assertTrue(any(":1 cita dotnet 8.0" in m for m in citadas))
        self.assertTrue(any(":3 cita mssqlserver 2014" in m for m in citadas))

    def test_citacao_historica_e_ignorada_mas_palavra_parecida_nao(self):
        self._escrever(os.path.join(self.plugins, "stack-node", "skills", "node", "SKILL.md"),
                       "antes do Node 25\ndesde o Node 25\n# update Node 25\nmigrate Node 25\n")
        citadas = [m for t, m in ac.levantar(HOJE, stacks=["node"], fonte_dir=self.fonte, gravar=False) if t == "versao_sem_suporte"]
        self.assertEqual(sorted(m.split(":")[1].split()[0] for m in citadas), ["3", "4"])

    def test_regrava_quando_muda_so_a_ultima_versao(self):
        ac.levantar(HOJE, stacks=["node"], fonte_dir=self.fonte)
        NODEJS_NOVO = [dict(c) for c in NODEJS]
        NODEJS_NOVO[1]["latest"] = "26.14.0"
        self._fonte("nodejs", NODEJS_NOVO)
        ac.levantar(HOJE, stacks=["node"], fonte_dir=self.fonte)
        self.assertIn("26.14.0", self._ler(self.node))

    def test_erro_de_rede_vira_falha_de_fonte(self):  # CA-6 pelo caminho da rede
        with mock.patch("urllib.request.urlopen", side_effect=http.client.IncompleteRead(b"")):
            with self.assertRaises(ac.Erro):  # nenhum produto respondeu
                ac.levantar(HOJE, stacks=["node"])
        self._fonte("python", "{não é json")
        achados = ac.levantar(HOJE, fonte_dir=self.fonte)
        self.assertTrue(any(t == "falha_fonte" and "JSON inválido" in m for t, m in achados))

    def test_falha_parcial_numa_stack_ainda_varre_os_outros_produtos(self):
        self._atual("node", "nodejs,python", BLOCO_NODE)
        antes = self._ler(self.node)
        achados = ac.levantar(HOJE, stacks=["node"], fonte_dir=self.fonte)
        self.assertEqual(self._ler(self.node), antes)
        self.assertTrue(any(t == "versao_sem_suporte" for t, _ in achados))

    def test_preserva_crlf_e_aponta_estrutura_no_modo_online(self):
        with open(self.node, encoding="utf-8") as f:
            texto = f.read()
        with open(self.node, "w", encoding="utf-8", newline="") as f:
            f.write(texto.replace("\n", "\r\n"))
        ac.levantar(HOJE, stacks=["node"], fonte_dir=self.fonte)
        with open(self.node, encoding="utf-8", newline="") as f:
            gravado = f.read()
        self.assertNotIn("\n", gravado.replace("\r\n", ""))
        self._escrever(self.py, "# sem metadados\n")
        achados = ac.levantar(HOJE, fonte_dir=self.fonte)
        self.assertTrue(any(t == "estrutura" and "stack-python" in m for t, m in achados))

    def test_stack_sem_produto_dispensa_tabela_mas_nao_a_revisao(self):  # demanda stacks-bash-git-linux, CA-2 e CA-3
        sem = "# Conhecimento atual: bash\n<!-- dev-flow:conhecimento revisado_em={r} produtos=- -->\n\n## Fontes oficiais\n- https://www.gnu.org/software/bash/\n\n## Versões\nSem ciclos publicados.\n\n## Mudanças a observar\n- nada\n"
        arq = os.path.join(self.plugins, "stack-bash", "referencias", "atual.md")
        self._escrever(arq, sem.format(r="2026-11-01"))
        self.assertEqual(ac.verificar(HOJE), [])
        with mock.patch.object(ac, "buscar", side_effect=AssertionError("não deveria consultar")):
            self.assertEqual(ac.levantar(HOJE, stacks=["bash"], gravar=False), [])
        self._escrever(arq, sem.format(r="2026-01-01"))
        with mock.patch.object(ac, "buscar", side_effect=AssertionError("não deveria consultar")):
            self.assertEqual([t for t, _ in ac.levantar(HOJE, stacks=["bash"], gravar=False)], ["revisao_vencida"])
        self.assertEqual(self._ler(arq), sem.format(r="2026-01-01"))
        self._escrever(arq, sem.format(r="2026-11-01").replace("produtos=-", "produtos=-,python"))
        self.assertTrue(any("não se mistura" in p for p in ac.verificar(HOJE)))
        self._escrever(arq, sem.format(r="2026-11-01").replace("Sem ciclos publicados.", "<!-- versoes:inicio -->\n<!-- versoes:fim -->"))
        self.assertTrue(any("não tem bloco de versões" in p for p in ac.verificar(HOJE)))
        os.remove(arq)
        self._atual("python", "", "")
        self.assertTrue(any("stack-python" in p and "produtos=" in p for p in ac.verificar(HOJE)))
        self._escrever(self.py, ATUAL.format(nome="python", revisado="2026-11-01", produtos="python", bloco="").replace(
            "<!-- versoes:inicio -->\n\n<!-- versoes:fim -->", ""))
        self.assertTrue(any("stack-python" in p and "versoes:inicio" in p for p in ac.verificar(HOJE)))

    def test_distribuicao_citada_por_codinome_tag_ou_runner(self):  # CA-4
        self._fonte("debian", [{"cycle": "13", "codename": "Trixie", "eol": "2030-06-30"},
                               {"cycle": "12", "codename": "Bookworm", "eol": "2028-06-30"},
                               {"cycle": "10", "codename": "Buster", "eol": "2024-06-30"}])
        self._fonte("ubuntu", [{"cycle": "24.04", "codename": "Noble Numbat", "lts": True, "eol": "2029-05-31"},
                               {"cycle": "20.04", "codename": "Focal Fossa", "lts": True, "eol": "2025-05-31"}])
        self._fonte("alpine-linux", [{"cycle": "3.22", "eol": "2027-05-01"}, {"cycle": "3.18", "eol": "2025-05-09"}])
        self._fonte("rhel", [{"cycle": "9", "eol": "2032-05-31"}, {"cycle": "7", "eol": "2024-06-30"}])
        self._fonte("git", [{"cycle": "2.56", "eol": False}, {"cycle": "2.46", "eol": "2025-07-08"}])
        self._atual("linux", "ubuntu,debian,alpine-linux,rhel", "")
        self._fonte("powershell", [{"cycle": "7.6", "lts": True, "eol": "2028-11-14"}, {"cycle": "7.2", "lts": True, "eol": "2024-11-08"}])
        self._atual("git", "git", "")
        self._atual("powershell", "powershell", "")
        self._escrever(os.path.join(self.plugins, "stack-linux", "templates", "x.yml"),
                       "a: debian:buster-slim\nb: node:20-buster\nc: python:3.12-slim-bookworm\n"
                       "runs-on: ubuntu-20.04\nd: ubuntu:focal\ne: node:20-alpine3.18\n"
                       "f: align-items:stretch\ng: Debian 12 e Ubuntu 24.04\nh: antes do Ubuntu 20.04\n"
                       "i: aspnet:6.0-focal\nj: node:lts-buster\nk: openjdk:11-jre-slim-buster\nl: buildpack-deps:buster\n"
                       "m: FROM ubi7/ubi-minimal e RHEL 9\nn: Git 2.46 e Git 2.56; a partir do Git 2.46\n"
                       "o: PowerShell 7.2, pwsh 7.6, Windows PowerShell 5.1 e powershell core 7.2\n"
                       "p: mcr.microsoft.com/powershell:lts-7.2-ubuntu-22.04\n")
        self._escrever(os.path.join(self.plugins, "stack-powershell", "templates", "x.ps1"), "\ufeff#requires -version 7.2\n")
        citadas = sorted(m.split(" cita ")[1] for t, m in ac.levantar(HOJE, stacks=["linux", "git", "powershell"], fonte_dir=self.fonte, gravar=False)
                         if t == "versao_sem_suporte")
        self.assertEqual(citadas, sorted(["debian buster, sem suporte"] * 5 + [
                                          "ubuntu 20.04, sem suporte", "ubuntu focal, sem suporte", "ubuntu focal, sem suporte",
                                          "alpine-linux 3.18, sem suporte", "rhel 7, sem suporte", "git 2.46, sem suporte",
                                          "powershell 7.2, sem suporte", "powershell 7.2, sem suporte",
                                          "powershell 7.2, sem suporte", "powershell 7.2, sem suporte"]))
        self.assertEqual(ac.nomes_do_ciclo({"cycle": "22.04", "codename": "Jammy Jellyfish"}), {"22.04", "jammy"})

    def test_codigos_de_saida_e_relatorio(self):
        rel = os.path.join(self.dir, "rel.md")
        self.assertEqual(self._main(*["--fonte-dir", self.fonte, "--stack", "node", "--hoje", "2026-11-19", "--relatorio", rel]), 2)
        self.assertIn("## Ciclos novos (1)", self._ler(rel))
        self.assertEqual(self._main(*["--verificar", "--hoje", "2026-11-19"]), 0)
        self.assertEqual(self._main(*["--verificar", "--hoje", "2027-11-19"]), 1)
        shutil.rmtree(self.plugins)
        self.assertEqual(self._main(*["--fonte-dir", self.fonte, "--hoje", "2026-11-19"]), 1)
        self.assertEqual(self._main("--hoje", "19/11/2026"), 1)


PLUGINS = os.path.join(RAIZ_REPO, "plugins")


def _ler_repo(*partes):
    with open(os.path.join(RAIZ_REPO, *partes), encoding="utf-8") as f:
        return f.read()


class ConhecimentoNoRepositorioTests(unittest.TestCase):
    def test_toda_stack_tem_atual_md_valido_e_citado(self):  # CA-1
        self.assertEqual(ac.verificar(dt.date.today(), max_dias=0), [])
        for pasta in sorted(os.listdir(PLUGINS)):
            if not pasta.startswith("stack-"):
                continue
            stack = pasta[len("stack-"):]
            skill = _ler_repo("plugins", pasta, "skills", stack, "SKILL.md")
            self.assertIn("`../../referencias/atual.md`", skill, pasta)
            self.assertIn("conhecimento.md", skill, pasta)
            d = ac.ler(os.path.join(PLUGINS, pasta, "referencias", "atual.md"))
            for produto in d["produtos"]:
                self.assertIn(produto, ac.PADROES, f"{pasta}: {produto} sem padrão de varredura")

    def test_max_dias_zero_ignora_idade(self):
        self.assertEqual(ac.verificar(dt.date(2099, 1, 1), max_dias=0), [])

    def test_especialistas_citam_projeto_primeiro(self):  # CA-2
        agentes = [os.path.join("plugins", "fluxo", "agents", a) for a in os.listdir(os.path.join(PLUGINS, "fluxo", "agents"))]
        agentes.append(os.path.join("plugins", "design", "agents", "designer.md"))
        agentes.append(os.path.join("plugins", "logs", "agents", "analista-de-logs.md"))
        for arq in agentes:
            texto = _ler_repo(arq)
            self.assertIn("## Conhecimento atual (projeto primeiro)", texto, arq)
            self.assertIn("fluxo/referencias/conhecimento.md", texto, arq)
            self.assertIn("conhecimento.novidades", texto, arq)

    def test_procedimento_cobre_os_quatro_passos_sem_depender_de_host(self):  # RF-2, CA-12
        texto = _ler_repo("plugins", "fluxo", "referencias", "conhecimento.md")
        for titulo in ("## 1. O projeto manda", "## 2. Versão em uso", "## 3. Documentação daquela versão", "## 4. Novidade"):
            self.assertIn(titulo, texto)
        self.assertIn("busca na web", texto)
        self.assertIn("pacote instalado", texto)
        self.assertIn("não confirmei", texto)

    def test_aprender_leva_aprendizado_de_stack_ao_atual_md(self):  # CA-10
        texto = _ler_repo("plugins", "fluxo", "skills", "aprender", "SKILL.md")
        linha = next(l for l in texto.splitlines() if "qualquer projeto daquela stack" in l)
        self.assertIn("referencias/atual.md", linha)
        self.assertIn("PR", linha)


class RevisaoPeriodicaTests(unittest.TestCase):  # CA-8
    def test_pipelines_agendadas_rodam_o_levantamento(self):
        for arq in ("azure-pipelines-conhecimento.yml", os.path.join(".github", "workflows", "conhecimento.yml")):
            texto = _ler_repo(arq)
            self.assertIn("cron:", texto, arq)
            self.assertIn("scripts/atualizar_conhecimento.py --sem-gravar --relatorio", texto, arq)
            self.assertNotIn("git push", texto, arq)
        self.assertIn("atualizar_conhecimento.py --verificar --max-dias 0", _ler_repo("azure-pipelines.yml"))

    def test_skill_de_manutencao_termina_em_branch_sem_merge(self):
        texto = _ler_repo(".claude", "skills", "atualizar-conhecimento", "SKILL.md")
        self.assertIn("name: atualizar-conhecimento", texto)
        self.assertIn("**nunca** faça merge, push", texto)
        self.assertIn("pr.md", texto)
        self.assertIn("avaliar_agentes.py", texto)
        self.assertIn("qualquer host", texto)


if __name__ == "__main__":
    unittest.main()
