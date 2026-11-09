"""Perfil do projeto (.claude/projeto.json): o contrato entre o processo genérico do plugin e cada projeto.

Uso: python -I perfil.py validar [dir]          confere o perfil e lista os problemas (código 1 se houver erro)
     python -I perfil.py mostrar [dir]          resumo legível
     python -I perfil.py obter <campo.a.b> [dir] valor de um campo (texto puro ou JSON)
     python -I perfil.py raiz [dir]             caminho da raiz do projeto (pasta que contém .claude/projeto.json)

A raiz é procurada subindo a partir de [dir] (padrão: diretório atual), e então em CLAUDE_PROJECT_DIR.
"""
import json
import os
import re
import sys

ARQUIVO = os.path.join(".claude", "projeto.json")
STACKS = {"dotnet", "sql", "front", "node", "python", "outra"}
RASTREADORES = {"local", "azure-boards"}
VALIDACOES = {"http", "sql", "navegador", "comando", "nenhuma"}
PUSH = {"humano", "permitido"}


def encontrar_raiz(inicio=None):
    candidatos = [os.path.abspath(inicio or os.getcwd())]
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        candidatos.append(os.path.abspath(os.environ["CLAUDE_PROJECT_DIR"]))
    for atual in candidatos:
        while True:
            if os.path.isfile(os.path.join(atual, ARQUIVO)):
                return atual
            pai = os.path.dirname(atual)
            if pai == atual:
                break
            atual = pai
    return None


def carregar(inicio=None):
    """Devolve (raiz, perfil) ou (None, {}) se não houver perfil. JSON inválido lança ValueError."""
    raiz = encontrar_raiz(inicio)
    if not raiz:
        return None, {}
    with open(os.path.join(raiz, ARQUIVO), encoding="utf-8") as f:
        try:
            return raiz, json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"{ARQUIVO} inválido: {e}") from e


def obter(perfil, campo, padrao=None):
    atual = perfil
    for parte in campo.split("."):
        if not isinstance(atual, dict) or parte not in atual:
            return padrao
        atual = atual[parte]
    return atual


def validar(perfil):
    """Lista de (nível, mensagem); nível 'erro' ou 'aviso'."""
    problemas = []

    def erro(m):
        problemas.append(("erro", m))

    def aviso(m):
        problemas.append(("aviso", m))

    if not isinstance(perfil.get("nome"), str) or not perfil["nome"].strip():
        erro("nome: obrigatório (texto).")
    stacks = perfil.get("stacks")
    if not isinstance(stacks, list) or not stacks:
        erro("stacks: obrigatório (lista não vazia).")
    else:
        for s in stacks:
            if s not in STACKS:
                aviso(f"stacks: '{s}' não tem plugin de stack ({', '.join(sorted(STACKS))}).")

    rastreador = perfil.get("rastreador") or {"tipo": "local"}
    tipo = rastreador.get("tipo")
    if tipo not in RASTREADORES:
        erro(f"rastreador.tipo: '{tipo}' inválido ({', '.join(sorted(RASTREADORES))}).")
    if tipo == "azure-boards":
        for c in ("org", "projeto"):
            if not rastreador.get(c):
                erro(f"rastreador.{c}: obrigatório quando tipo = azure-boards.")

    comandos = perfil.get("comandos") or {}
    if not isinstance(comandos, dict):
        erro("comandos: deve ser objeto.")
    elif not comandos.get("teste"):
        aviso("comandos.teste: sem comando de teste, o ciclo da task não tem como provar que funciona.")

    validacao = perfil.get("validacao") or {"tipo": "nenhuma"}
    if validacao.get("tipo") not in VALIDACOES:
        erro(f"validacao.tipo: '{validacao.get('tipo')}' inválido ({', '.join(sorted(VALIDACOES))}).")
    if validacao.get("tipo") == "http" and not validacao.get("base_url"):
        erro("validacao.base_url: obrigatório quando tipo = http.")

    git = perfil.get("git") or {}
    if git.get("push", "humano") not in PUSH:
        erro(f"git.push: '{git.get('push')}' inválido ({', '.join(sorted(PUSH))}).")

    protecao = perfil.get("protecao") or {}
    for chave in ("textos_proibidos", "gerados"):
        for i, item in enumerate(protecao.get(chave) or []):
            if not isinstance(item, dict) or not item.get("regex"):
                erro(f"protecao.{chave}[{i}]: precisa de 'regex'.")
                continue
            try:
                re.compile(item["regex"])
            except re.error as e:
                erro(f"protecao.{chave}[{i}].regex: {e}")
    return problemas


def resumo(raiz, perfil):
    r = perfil.get("rastreador") or {"tipo": "local"}
    v = perfil.get("validacao") or {"tipo": "nenhuma"}
    linhas = [
        f"Projeto: {perfil.get('nome')} ({', '.join(perfil.get('stacks') or [])})",
        f"Raiz: {raiz}",
        f"Especificações: {perfil.get('docs', 'docs/demandas')}",
        f"Rastreador: {r.get('tipo')}" + (f" {r.get('org')}/{r.get('projeto')}, item raiz {r.get('item_raiz')}" if r.get("tipo") == "azure-boards" else ""),
        f"Validação: {v.get('tipo')}" + (f" em {v.get('base_url')}" if v.get("base_url") else ""),
        f"Git: base {obter(perfil, 'git.branch_base', 'main')}, push {obter(perfil, 'git.push', 'humano')}, commit por task {obter(perfil, 'git.commit_por_task', True)}",
    ]
    for nome, cmd in (perfil.get("comandos") or {}).items():
        linhas.append(f"  {nome}: {cmd}")
    return "\n".join(linhas)


def main(argv):
    if len(argv) < 2 or argv[1] not in ("validar", "mostrar", "obter", "raiz"):
        sys.exit(__doc__)
    acao = argv[1]
    campo = argv[2] if acao == "obter" and len(argv) > 2 else None
    inicio = argv[3] if acao == "obter" and len(argv) > 3 else (argv[2] if acao != "obter" and len(argv) > 2 else None)
    try:
        raiz, perfil = carregar(inicio)
    except ValueError as e:
        print(e)
        return 1
    if not raiz:
        print("Sem .claude/projeto.json a partir deste diretório. Rode /fluxo:iniciar.")
        return 2
    if acao == "raiz":
        print(raiz)
    elif acao == "mostrar":
        print(resumo(raiz, perfil))
    elif acao == "obter":
        valor = obter(perfil, campo or "")
        print(valor if isinstance(valor, str) else json.dumps(valor, ensure_ascii=False))
        return 0 if valor is not None else 1
    else:
        problemas = validar(perfil)
        for nivel, msg in problemas:
            print(f"[{nivel}] {msg}")
        if not problemas:
            print("perfil ok")
        return 1 if any(n == "erro" for n, _ in problemas) else 0
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
