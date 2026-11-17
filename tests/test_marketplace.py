"""Consistência do marketplace: manifestos, skills, agentes e stacks declaradas no perfil."""
import glob
import json
import os
import re
import unittest

from apoio import FLUXO, RAIZ_REPO

import perfil

PLUGINS = os.path.join(RAIZ_REPO, "plugins")


def _ler(arq):
    with open(arq, encoding="utf-8") as f:
        return f.read()


def _frontmatter(texto):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", texto, re.S)
    if not m:
        return None
    campos = {}
    for linha in m.group(1).splitlines():
        if ":" in linha and not linha.startswith(" "):
            chave, valor = linha.split(":", 1)
            campos[chave.strip()] = valor.strip()
    return campos


class MarketplaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.marketplace = json.loads(_ler(os.path.join(RAIZ_REPO, ".claude-plugin", "marketplace.json")))

    def test_todo_plugin_registrado_com_versao_igual(self):
        registrados = {p["name"]: p for p in self.marketplace["plugins"]}
        pastas = {os.path.basename(p) for p in glob.glob(os.path.join(PLUGINS, "*")) if os.path.isdir(p)}
        self.assertEqual(set(registrados), pastas)
        for nome, item in registrados.items():
            manifesto = json.loads(_ler(os.path.join(PLUGINS, nome, ".claude-plugin", "plugin.json")))
            self.assertEqual(manifesto["name"], nome)
            self.assertEqual(manifesto["version"], item["version"], nome)
            self.assertEqual(item["source"], f"./plugins/{nome}")

    def test_skills_e_agentes_tem_frontmatter(self):
        arquivos = glob.glob(os.path.join(PLUGINS, "*", "skills", "*", "SKILL.md"))
        agentes = glob.glob(os.path.join(PLUGINS, "*", "agents", "*.md"))
        self.assertTrue(arquivos and agentes)
        for arq in arquivos + agentes:
            campos = _frontmatter(_ler(arq))
            self.assertIsNotNone(campos, arq)
            self.assertTrue(campos.get("name"), arq)
            self.assertGreater(len(campos.get("description", "")), 60, arq)
        for arq in arquivos:
            self.assertEqual(_frontmatter(_ler(arq))["name"], os.path.basename(os.path.dirname(arq)), arq)

    def test_toda_stack_do_perfil_tem_plugin_com_as_tres_secoes(self):
        for stack in sorted(perfil.STACKS - {"outra"}):
            arq = os.path.join(PLUGINS, f"stack-{stack}", "skills", stack, "SKILL.md")
            self.assertTrue(os.path.isfile(arq), f"falta plugin da stack {stack}")
            texto = _ler(arq)
            titulos = re.findall(r"^## (.+?)\s*$", texto, re.M)
            self.assertTrue(any(t in ("Testar", "Validar") or t.startswith("Validar") for t in titulos), arq)
            self.assertEqual(titulos[-1], "Checklist de revisão", arq)
            self.assertGreaterEqual(len(re.findall(r"^\d+\. ", texto.split("## Checklist de revisão")[1], re.M)), 5, arq)

    def test_schema_e_perfil_concordam(self):
        schema = json.loads(_ler(os.path.join(FLUXO, "schema", "projeto.schema.json")))
        props = schema["properties"]
        self.assertEqual(set(props["stacks"]["items"]["enum"]), perfil.STACKS)
        self.assertEqual(set(props["ci"]["properties"]["provedor"]["enum"]), perfil.PROVEDORES_CI)
        self.assertEqual(set(props["infra"]["properties"]["nuvem"]["enum"]), perfil.NUVENS)
        self.assertEqual(set(props["infra"]["properties"]["execucao"]["items"]["enum"]), perfil.EXECUCOES)

    def test_provedor_de_ci_tem_plugin(self):
        mapa = {"azure-pipelines": "azure-pipelines", "github-actions": "github-actions", "gitlab-ci": "gitlab-ci"}
        for provedor in perfil.PROVEDORES_CI - {"nenhum"}:
            self.assertTrue(os.path.isdir(os.path.join(PLUGINS, mapa[provedor], "skills")), provedor)

    def test_referencias_relativas_das_skills_existem(self):
        for arq in glob.glob(os.path.join(PLUGINS, "*", "skills", "*", "SKILL.md")):
            base = os.path.dirname(arq)
            for ref in re.findall(r"`(\.\./\.\./[^`\s]+)`", _ler(arq)):
                if "<" in ref or "{" in ref:
                    continue
                self.assertTrue(os.path.exists(os.path.normpath(os.path.join(base, ref))), f"{arq}: {ref}")


if __name__ == "__main__":
    unittest.main()
