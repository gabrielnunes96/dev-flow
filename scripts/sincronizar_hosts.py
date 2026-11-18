#!/usr/bin/env python3
"""Gera os manifests Cursor a partir da fonte canônica Claude Code.

Canônico:
  .claude-plugin/marketplace.json
  plugins/<nome>/.claude-plugin/plugin.json
  plugins/fluxo/hooks/hooks.json

Gerado (não editar à mão):
  .cursor-plugin/marketplace.json
  plugins/<nome>/.cursor-plugin/plugin.json
  plugins/fluxo/hooks/hooks.cursor.json

Uso:
  python -I scripts/sincronizar_hosts.py
  python -I scripts/sincronizar_hosts.py --check   # exit 1 se desatualizado
"""
from __future__ import annotations

import argparse
import json
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLAUDE_MP = os.path.join(RAIZ, ".claude-plugin", "marketplace.json")
CURSOR_MP = os.path.join(RAIZ, ".cursor-plugin", "marketplace.json")


def _ler_json(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _escrever_json(caminho, dados):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    texto = json.dumps(dados, ensure_ascii=False, indent=2) + "\n"
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)
    return texto


def _source_relativo(source):
    """./plugins/fluxo → plugins/fluxo (schema Cursor prefere path sem ./)."""
    s = source.strip()
    if s.startswith("./"):
        s = s[2:]
    return s


def marketplace_cursor(claude):
    # Com metadata.pluginRoot = "plugins", o source é só o nome da pasta.
    plugins = []
    for item in claude["plugins"]:
        entry = {
            "name": item["name"],
            "source": item["name"],
            "description": item.get("description", ""),
        }
        plugins.append(entry)
    out = {
        "name": claude["name"],
        "owner": claude.get("owner", {"name": "dev-flow"}),
        "metadata": {
            "description": claude.get("metadata", {}).get("description", ""),
            "version": claude.get("metadata", {}).get("version", "0.0.0"),
            "pluginRoot": "plugins",
        },
        "plugins": plugins,
    }
    return out


def plugin_cursor(claude_plugin, nome, pasta_plugin):
    autor = claude_plugin.get("author") or {}
    out = {
        "name": nome,
        "description": claude_plugin.get("description", ""),
        "version": claude_plugin.get("version", "0.0.0"),
        "author": {"name": autor.get("name", "dev-flow")},
    }
    if claude_plugin.get("keywords"):
        out["keywords"] = list(claude_plugin["keywords"])
    hooks_cursor_path = os.path.join(pasta_plugin, "hooks", "hooks.cursor.json")
    if os.path.isfile(hooks_cursor_path):
        out["hooks"] = "hooks/hooks.cursor.json"
    return out


def hooks_cursor():
    """Mesmos scripts do hooks.json Claude, no formato nativo Cursor."""
    return {
        "version": 1,
        "hooks": {
            "preToolUse": [
                {
                    "matcher": "Shell|Read|Grep|Write|Task",
                    "command": 'python -I "${CURSOR_PLUGIN_ROOT}/hooks/guard.py"',
                    "timeout": 30,
                }
            ],
            "sessionStart": [
                {
                    "command": 'python -I "${CURSOR_PLUGIN_ROOT}/hooks/contexto.py"',
                    "timeout": 15,
                }
            ],
        },
    }


def gerar():
    claude = _ler_json(CLAUDE_MP)
    gerados = {}
    gerados[CURSOR_MP] = marketplace_cursor(claude)
    for item in claude["plugins"]:
        nome = item["name"]
        pasta = os.path.join(RAIZ, _source_relativo(item["source"]))
        claude_pj = _ler_json(os.path.join(pasta, ".claude-plugin", "plugin.json"))
        if claude_pj.get("name") != nome:
            raise SystemExit(f"nome divergente em {nome}: plugin.json={claude_pj.get('name')}")
        destino = os.path.join(pasta, ".cursor-plugin", "plugin.json")
        gerados[destino] = plugin_cursor(claude_pj, nome, pasta)
    gerados[os.path.join(RAIZ, "plugins", "fluxo", "hooks", "hooks.cursor.json")] = hooks_cursor()
    return gerados


def _igual_disco(caminho, dados):
    if not os.path.isfile(caminho):
        return False
    atual = _ler_json(caminho)
    return atual == dados


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="só verifica; não escreve")
    args = p.parse_args(argv)
    gerados = gerar()
    divergentes = [c for c, d in gerados.items() if not _igual_disco(c, d)]
    if args.check:
        if divergentes:
            print("Manifests Cursor desatualizados:")
            for c in divergentes:
                print(f"  {os.path.relpath(c, RAIZ)}")
            print("Rode: python -I scripts/sincronizar_hosts.py")
            return 1
        print(f"ok: {len(gerados)} arquivo(s) Cursor alinhados ao Claude")
        return 0
    for caminho, dados in gerados.items():
        _escrever_json(caminho, dados)
        print(os.path.relpath(caminho, RAIZ))
    print(f"sincronizados: {len(gerados)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
