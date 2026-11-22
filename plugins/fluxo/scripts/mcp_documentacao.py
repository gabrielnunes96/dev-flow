#!/usr/bin/env python3
"""Gera a configuração de MCP de documentação para as stacks do perfil (catálogo em ../referencias/documentacao.md).

Uso: python -I mcp_documentacao.py --host claude|cursor [--dir PASTA] [--stack X ...] [--com-chave]
  --host       claude → trecho de .mcp.json ("type": "http"); cursor → trecho de .cursor/mcp.json (só "url")
  --dir        onde procurar .claude/projeto.json (padrão: diretório atual, subindo)
  --stack      usa estas stacks em vez das do perfil (repetível)
  --com-chave  inclui o cabeçalho Authorization com a variável de ambiente da chave (nunca o valor)

Imprime {"mcpServers": {...}} para o usuário mesclar na configuração do host. Saída 0 ok, 1 erro
(sem perfil e sem --stack, catálogo mal formado). Não grava nada.
"""
import argparse
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import perfil as perfil_mod  # noqa: E402

CATALOGO = os.path.normpath(os.path.join(AQUI, "..", "referencias", "documentacao.md"))


class Erro(Exception):
    pass


def ler_catalogo(arq=CATALOGO):
    """Lista de {nome, url, chave (variável ou None), stacks (set; '*' = todas)}."""
    with open(arq, encoding="utf-8") as f:
        texto = f.read()
    if "## Catálogo" not in texto:
        raise Erro(f"{arq}: falta a seção '## Catálogo'")
    secao = texto.split("## Catálogo", 1)[1].split("\n## ", 1)[0]
    itens = []
    for linha in secao.splitlines():
        cel = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(cel) < 6 or not cel[0].startswith("`"):
            continue
        nome = cel[0].strip("`")
        if not re.fullmatch(r"[a-z0-9-]+", nome) or not cel[1].startswith("https://"):
            raise Erro(f"{arq}: linha mal formada: {linha.strip()}")
        chave = re.search(r"`([A-Z][A-Z0-9_]*)`", cel[2])
        itens.append({"nome": nome, "url": cel[1], "chave": chave.group(1) if chave else None,
                      "stacks": {s.strip() for s in cel[4].split(",") if s.strip()}})
    if not itens:
        raise Erro(f"{arq}: catálogo vazio")
    return itens


def configurar(itens, stacks, host, com_chave=False):
    servidores = {}
    for item in itens:
        if "*" not in item["stacks"] and not (item["stacks"] & set(stacks)):
            continue
        if host == "claude":
            cfg = {"type": "http", "url": item["url"]}
            ref = "${%s}" % item["chave"] if item["chave"] else None
        else:
            cfg = {"url": item["url"]}
            ref = "${env:%s}" % item["chave"] if item["chave"] else None
        if com_chave and ref:
            cfg["headers"] = {"Authorization": f"Bearer {ref}"}
        servidores[item["nome"]] = cfg
    return {"mcpServers": servidores}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", choices=("claude", "cursor"), required=True)
    ap.add_argument("--dir")
    ap.add_argument("--stack", action="append")
    ap.add_argument("--com-chave", action="store_true")
    args = ap.parse_args(argv)
    try:
        stacks = args.stack
        if not stacks:
            try:
                raiz, perfil = perfil_mod.carregar(args.dir)
            except ValueError as e:
                raise Erro(str(e)) from e
            if not raiz:
                raise Erro("sem .claude/projeto.json (rode a skill iniciar ou informe --stack)")
            stacks = perfil.get("stacks") or []
        saida = configurar(ler_catalogo(), stacks, args.host, args.com_chave)
    except (Erro, OSError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    print(json.dumps(saida, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    for fluxo in (sys.stdout, sys.stderr):
        fluxo.reconfigure(encoding="utf-8")
    sys.exit(main())
