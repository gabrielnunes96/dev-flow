"""Portabilidade: manifests Cursor espelham o Claude; export de skills funciona."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from apoio import RAIZ_REPO

SCRIPTS = os.path.join(RAIZ_REPO, "scripts")
SYNC = os.path.join(SCRIPTS, "sincronizar_hosts.py")
EXPORT = os.path.join(SCRIPTS, "exportar_skills.py")
INSTALAR = os.path.join(SCRIPTS, "instalar_em_projeto.py")


def _ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def _json(caminho):
    return json.loads(_ler(caminho))


class PortabilidadeTests(unittest.TestCase):
    def test_sincronizar_hosts_check_ok(self):
        r = subprocess.run(
            [sys.executable, "-I", SYNC, "--check"],
            cwd=RAIZ_REPO,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_marketplace_cursor_espelha_claude(self):
        claude = _json(os.path.join(RAIZ_REPO, ".claude-plugin", "marketplace.json"))
        cursor = _json(os.path.join(RAIZ_REPO, ".cursor-plugin", "marketplace.json"))
        self.assertEqual(cursor["name"], claude["name"])
        self.assertEqual(cursor["metadata"]["version"], claude["metadata"]["version"])
        self.assertEqual(cursor["metadata"].get("pluginRoot"), "plugins")
        nomes_c = [p["name"] for p in claude["plugins"]]
        nomes_u = [p["name"] for p in cursor["plugins"]]
        self.assertEqual(nomes_u, nomes_c)
        for c, u in zip(claude["plugins"], cursor["plugins"]):
            self.assertEqual(u["name"], c["name"])
            self.assertEqual(u["source"], c["name"])
            self.assertEqual(u["description"], c["description"])
            pasta = os.path.join(RAIZ_REPO, "plugins", c["name"])
            pj = _json(os.path.join(pasta, ".cursor-plugin", "plugin.json"))
            self.assertEqual(pj["name"], c["name"])
            self.assertEqual(pj["version"], c["version"])
            claude_pj = _json(os.path.join(pasta, ".claude-plugin", "plugin.json"))
            self.assertEqual(pj["version"], claude_pj["version"])

    def test_fluxo_cursor_aponta_hooks(self):
        pj = _json(os.path.join(RAIZ_REPO, "plugins", "fluxo", ".cursor-plugin", "plugin.json"))
        self.assertEqual(pj.get("hooks"), "hooks/hooks.cursor.json")
        hooks = _json(os.path.join(RAIZ_REPO, "plugins", "fluxo", "hooks", "hooks.cursor.json"))
        self.assertIn("preToolUse", hooks["hooks"])
        self.assertIn("sessionStart", hooks["hooks"])
        self.assertTrue(os.path.isfile(os.path.join(RAIZ_REPO, "plugins", "fluxo", "referencias", "hosts.md")))

    def test_exportar_formato_plugin(self):
        with tempfile.TemporaryDirectory(prefix="export-") as tmp:
            r = subprocess.run(
                [sys.executable, "-I", EXPORT, "--destino", tmp, "--plugins", "fluxo,stack-python", "--formato", "plugin"],
                cwd=RAIZ_REPO,
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(os.path.isfile(os.path.join(tmp, "fluxo", "skills", "iniciar", "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(tmp, "fluxo", "scripts", "perfil.py")))
            self.assertTrue(os.path.isfile(os.path.join(tmp, "stack-python", "skills", "python", "SKILL.md")))
            # path relativo da skill continua válido
            skill = os.path.join(tmp, "fluxo", "skills", "iniciar", "SKILL.md")
            scripts = os.path.normpath(os.path.join(os.path.dirname(skill), "../../scripts/perfil.py"))
            self.assertTrue(os.path.isfile(scripts))

    def test_exportar_formato_agents_skills(self):
        with tempfile.TemporaryDirectory(prefix="export-as-") as tmp:
            r = subprocess.run(
                [sys.executable, "-I", EXPORT, "--destino", tmp, "--plugins", "fluxo", "--formato", "agents-skills"],
                cwd=RAIZ_REPO,
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            skill = os.path.join(tmp, "iniciar", "SKILL.md")
            self.assertTrue(os.path.isfile(skill))
            texto = _ler(skill)
            self.assertIn("../_runtime/fluxo/", texto)
            self.assertIn("../_runtime/fluxo/templates/projeto.json", texto)
            self.assertTrue(os.path.isfile(os.path.join(tmp, "_runtime", "fluxo", "scripts", "perfil.py")))
            self.assertNotIn("../../scripts/", texto)
            self.assertNotIn("../../templates/", texto)

    def test_instalar_em_projeto_azure(self):
        with tempfile.TemporaryDirectory(prefix="proj-azure-") as projeto:
            os.makedirs(os.path.join(projeto, ".claude"))
            with open(os.path.join(projeto, ".claude", "projeto.json"), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "nome": "Demo",
                        "stacks": ["dotnet"],
                        "docs": "docs/demandas",
                        "rastreador": {"tipo": "azure-boards"},
                        "ci": {"provedor": "azure-pipelines"},
                        "git": {"branch_base": "main"},
                    },
                    f,
                )
            r = subprocess.run(
                [sys.executable, "-I", INSTALAR, "--projeto", projeto, "--azure"],
                cwd=RAIZ_REPO,
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            skills = os.path.join(projeto, ".agents", "skills")
            self.assertTrue(os.path.isfile(os.path.join(skills, "iniciar", "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(skills, "dotnet", "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(skills, "boards", "SKILL.md")))
            self.assertTrue(os.path.isfile(os.path.join(skills, "pipeline", "SKILL.md")))
            hooks = _json(os.path.join(projeto, ".cursor", "hooks.json"))
            self.assertIn("guard.py", hooks["hooks"]["preToolUse"][0]["command"])
            self.assertTrue(os.path.isfile(os.path.join(skills, "_runtime", "fluxo", "hooks", "guard.py")))


if __name__ == "__main__":
    unittest.main()
