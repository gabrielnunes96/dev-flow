#!/usr/bin/env python3
"""Exporta plugins do dev-flow para um projeto consumidor (modo vendor / Agent Skills).

Formatos:
  plugin         — copia a árvore do plugin (skills, scripts, agents, …) para
                   <destino>/<nome-do-plugin>/  (padrão; preserva ../../scripts)
  agents-skills  — skills achatadas em <destino>/<skill>/ + runtime compartilhado
                   em <destino>/_runtime/<plugin>/; reescreve paths ../../…

Uso:
  python -I scripts/exportar_skills.py --destino /proj/.agents/dev-flow --plugins fluxo,stack-python
  python -I scripts/exportar_skills.py --destino /proj/.agents/skills --plugins fluxo --formato agents-skills
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLAUDE_MP = os.path.join(RAIZ, ".claude-plugin", "marketplace.json")

# Pastas do plugin que as skills/agentes precisam em runtime.
COPIAR = (
    "skills",
    "scripts",
    "agents",
    "hooks",
    "templates",
    "schema",
    "referencias",
    "assets",
)


def _plugins_catalogo():
    with open(CLAUDE_MP, encoding="utf-8") as f:
        mp = json.load(f)
    out = {}
    for item in mp["plugins"]:
        src = item["source"].lstrip("./")
        out[item["name"]] = os.path.join(RAIZ, src)
    return out


def _copiar_plugin(origem, destino_plugin):
    if os.path.isdir(destino_plugin):
        shutil.rmtree(destino_plugin)
    os.makedirs(destino_plugin, exist_ok=True)
    copiados = []
    for nome in COPIAR:
        src = os.path.join(origem, nome)
        if not os.path.exists(src):
            continue
        dst = os.path.join(destino_plugin, nome)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        copiados.append(nome)
    # Manifests leves para identificação (opcional)
    for rel in (".claude-plugin/plugin.json", ".cursor-plugin/plugin.json"):
        src = os.path.join(origem, rel)
        if os.path.isfile(src):
            dst = os.path.join(destino_plugin, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    return copiados


_RE_REL = re.compile(r"(\.\./\.\./)([^\s`\"')]+)")


def _reescrever_skill(texto, plugin_nome):
    """../../scripts/x → ../_runtime/<plugin>/scripts/x (com ou sem backticks)."""

    def subst(m):
        resto = m.group(2)
        return f"../_runtime/{plugin_nome}/{resto}"

    return _RE_REL.sub(subst, texto)


def exportar_plugin(destino, nomes, formato):
    catalogo = _plugins_catalogo()
    desconhecidos = [n for n in nomes if n not in catalogo]
    if desconhecidos:
        raise SystemExit(f"plugins inexistentes: {', '.join(desconhecidos)}")
    os.makedirs(destino, exist_ok=True)
    resumo = []
    for nome in nomes:
        origem = catalogo[nome]
        if formato == "plugin":
            dest = os.path.join(destino, nome)
            partes = _copiar_plugin(origem, dest)
            resumo.append(f"{nome} → {dest} ({', '.join(partes) or 'vazio'})")
            continue
        # agents-skills
        runtime = os.path.join(destino, "_runtime", nome)
        partes = _copiar_plugin(origem, runtime)
        skills_dir = os.path.join(origem, "skills")
        if os.path.isdir(skills_dir):
            for skill in sorted(os.listdir(skills_dir)):
                skill_src = os.path.join(skills_dir, skill)
                skill_md = os.path.join(skill_src, "SKILL.md")
                if not os.path.isfile(skill_md):
                    continue
                dest_skill = os.path.join(destino, skill)
                if os.path.isdir(dest_skill):
                    shutil.rmtree(dest_skill)
                shutil.copytree(skill_src, dest_skill)
                md_path = os.path.join(dest_skill, "SKILL.md")
                with open(md_path, encoding="utf-8") as f:
                    texto = f.read()
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(_reescrever_skill(texto, nome))
                resumo.append(f"skill {skill} ← {nome}")
        else:
            resumo.append(f"{nome}: sem skills ({', '.join(partes)})")
    return resumo


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--destino", required=True, help="pasta de destino no projeto consumidor")
    p.add_argument(
        "--plugins",
        default="fluxo",
        help="lista separada por vírgula (padrão: fluxo)",
    )
    p.add_argument(
        "--formato",
        choices=("plugin", "agents-skills"),
        default="plugin",
        help="plugin = árvore completa; agents-skills = skills achatadas + _runtime",
    )
    args = p.parse_args(argv)
    nomes = [n.strip() for n in args.plugins.split(",") if n.strip()]
    if not nomes:
        raise SystemExit("informe ao menos um plugin em --plugins")
    destino = os.path.abspath(args.destino)
    for linha in exportar_plugin(destino, nomes, args.formato):
        print(linha)
    print(f"ok: {len(nomes)} plugin(s) → {destino} ({args.formato})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
