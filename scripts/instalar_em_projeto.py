#!/usr/bin/env python3
"""Instala o DevFlow (skills + runtime + hooks Cursor) em um projeto consumidor.

Copia skills no formato Agent Skills para <projeto>/.agents/skills e, se ainda
não existir, grava .cursor/hooks.json apontando para o runtime exportado.
Idempotente: seguro reexecutar.

Uso:
  python -I scripts/instalar_em_projeto.py --projeto /caminho/do/produto
  python -I scripts/instalar_em_projeto.py --projeto /caminho/do/produto --plugins fluxo,stack-dotnet
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exportar_skills import _plugins_catalogo, exportar_plugin  # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATE_HOOKS = os.path.join(RAIZ, "plugins", "fluxo", "templates", "hooks.cursor.json")
PERFIL_REL = os.path.join(".claude", "projeto.json")
DESTINO_SKILLS_REL = os.path.join(".agents", "skills")
HOOKS_REL = os.path.join(".cursor", "hooks.json")

# Paths relativos à raiz do projeto consumidor (Cursor roda hooks a partir dela).
RUNTIME_FLUXO = os.path.join(".agents", "skills", "_runtime", "fluxo").replace("\\", "/")


def _ler_json(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _escrever_json(caminho, dados):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _plugins_do_perfil(projeto):
    """Retorna lista de plugins a partir de .claude/projeto.json, ou None se ausente."""
    caminho = os.path.join(projeto, PERFIL_REL)
    if not os.path.isfile(caminho):
        return None
    perfil = _ler_json(caminho)
    catalogo = _plugins_catalogo()
    nomes = ["fluxo"]
    avisos = []
    for stack in perfil.get("stacks") or []:
        if not isinstance(stack, str) or not stack.strip():
            continue
        nome = f"stack-{stack.strip()}"
        if nome not in catalogo:
            avisos.append(f"stack '{stack}' sem plugin {nome} no marketplace — ignorada")
            continue
        if nome not in nomes:
            nomes.append(nome)
    return nomes, avisos


def _resolver_plugins(projeto, plugins_arg):
    """Devolve (nomes, avisos)."""
    avisos = []
    if plugins_arg is not None:
        nomes = [n.strip() for n in plugins_arg.split(",") if n.strip()]
        if not nomes:
            raise SystemExit("informe ao menos um plugin em --plugins")
        return nomes, avisos

    resolvido = _plugins_do_perfil(projeto)
    if resolvido is None:
        avisos.append(
            "sem .claude/projeto.json — instalando só 'fluxo'. "
            "Passe --plugins ou rode /iniciar no projeto depois."
        )
        return ["fluxo"], avisos
    nomes, avisos_perfil = resolvido
    avisos.extend(avisos_perfil)
    return nomes, avisos


def _hooks_vendor():
    """hooks.cursor.json do template, com paths relativos ao runtime exportado."""
    dados = _ler_json(TEMPLATE_HOOKS)
    # Reescreve ${DEV_FLOW_FLUXO}/… → .agents/skills/_runtime/fluxo/…
    def _cmd(script):
        return f'python -I "{RUNTIME_FLUXO}/hooks/{script}"'

    hooks = dados.get("hooks") or {}
    for lista in hooks.values():
        if not isinstance(lista, list):
            continue
        for item in lista:
            if not isinstance(item, dict) or "command" not in item:
                continue
            cmd = item["command"]
            if "guard.py" in cmd:
                item["command"] = _cmd("guard.py")
            elif "contexto.py" in cmd:
                item["command"] = _cmd("contexto.py")
    return dados


def instalar(projeto, plugins_arg=None):
    projeto = os.path.abspath(projeto)
    if not os.path.isdir(projeto):
        raise SystemExit(f"projeto não é um diretório: {projeto}")

    nomes, avisos = _resolver_plugins(projeto, plugins_arg)
    for a in avisos:
        print(f"aviso: {a}", file=sys.stderr)

    destino = os.path.join(projeto, DESTINO_SKILLS_REL)
    resumo = exportar_plugin(destino, nomes, "agents-skills")
    for linha in resumo:
        print(linha)
    print(f"ok: skills → {destino} (agents-skills; {', '.join(nomes)})")

    hooks_path = os.path.join(projeto, HOOKS_REL)
    if os.path.isfile(hooks_path):
        print(f"hooks: mantido {hooks_path} (já existia)")
    else:
        _escrever_json(hooks_path, _hooks_vendor())
        print(f"hooks: criado {hooks_path}")
        print(
            f"       aponta para {RUNTIME_FLUXO}/hooks/ "
            "(sem precisar de DEV_FLOW_FLUXO)."
        )

    print()
    print("Próximos passos:")
    print(f"  1. Commit de {DESTINO_SKILLS_REL}/ e, se novo, {HOOKS_REL}")
    print(f"     (+ {PERFIL_REL} se ainda não versionado).")
    print("  2. Push do projeto consumidor.")
    print("  3. Abra um novo Cursor Agent nesse repositório.")
    print('  4. Peça: "iniciar o fluxo".')
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projeto", required=True, help="raiz do projeto consumidor")
    p.add_argument(
        "--plugins",
        default=None,
        help="lista separada por vírgula; padrão = fluxo + stacks do perfil",
    )
    args = p.parse_args(argv)
    return instalar(args.projeto, args.plugins)


if __name__ == "__main__":
    sys.exit(main())
