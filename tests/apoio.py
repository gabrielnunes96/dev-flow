import json
import os
import shutil
import sys
import tempfile

RAIZ_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FLUXO = os.path.join(RAIZ_REPO, "plugins", "fluxo")
sys.path.insert(0, os.path.join(FLUXO, "scripts"))
sys.path.insert(0, os.path.join(FLUXO, "hooks"))


class ProjetoTemporario:
    """Pasta temporária com .claude/projeto.json; restaura cwd e CLAUDE_PROJECT_DIR ao sair."""

    def __init__(self, perfil=None):
        self.perfil = perfil

    def __enter__(self):
        self.raiz = tempfile.mkdtemp(prefix="fluxo-")
        if self.perfil is not None:
            os.makedirs(os.path.join(self.raiz, ".claude"))
            with open(os.path.join(self.raiz, ".claude", "projeto.json"), "w", encoding="utf-8") as f:
                json.dump(self.perfil, f)
        self._cwd = os.getcwd()
        self._env = os.environ.pop("CLAUDE_PROJECT_DIR", None)
        os.chdir(self.raiz)
        return self.raiz

    def __exit__(self, *_):
        os.chdir(self._cwd)
        if self._env is not None:
            os.environ["CLAUDE_PROJECT_DIR"] = self._env
        shutil.rmtree(self.raiz, ignore_errors=True)
