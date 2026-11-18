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
STACKS = {"dotnet", "sql", "front", "node", "python", "java", "go", "postgres", "mysql", "mongodb", "redis",
          "docker", "kubernetes", "terraform", "outra"}
RASTREADORES = {"local", "azure-boards"}
VALIDACOES = {"http", "sql", "navegador", "comando", "nenhuma"}
PUSH = {"humano", "permitido"}
PLATAFORMAS = {"web", "ios", "android", "desktop"}
PROVEDORES_CI = {"azure-pipelines", "github-actions", "gitlab-ci", "nenhum"}
NUVENS = {"azure", "aws", "gcp", "on-premise", "outra"}
EXECUCOES = {"kubernetes", "compose", "app-service", "container-apps", "ecs", "lambda", "functions", "cloud-run", "vm", "outra"}
# Stack de infraestrutura que exige a declaração correspondente em infra.execucao.
INFRA_EXIGE = {"kubernetes": "kubernetes"}


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

    design = perfil.get("design")
    if design is not None:
        if not isinstance(design, dict):
            erro("design: deve ser objeto.")
        else:
            for c in ("tokens", "sistema"):
                if c in design and not isinstance(design[c], str):
                    erro(f"design.{c}: deve ser texto.")
            for p in design.get("plataformas") or []:
                if p not in PLATAFORMAS:
                    erro(f"design.plataformas: '{p}' inválida ({', '.join(sorted(PLATAFORMAS))}).")

    ci = perfil.get("ci")
    if ci is not None:
        if not isinstance(ci, dict):
            erro("ci: deve ser objeto.")
        else:
            if ci.get("provedor", "nenhum") not in PROVEDORES_CI:
                erro(f"ci.provedor: '{ci.get('provedor')}' inválido ({', '.join(sorted(PROVEDORES_CI))}).")
            for c in ("arquivos", "ambientes"):
                if c in ci and (not isinstance(ci[c], list) or not all(isinstance(x, str) for x in ci[c])):
                    erro(f"ci.{c}: deve ser lista de textos.")
            amb = ci.get("ambientes") or []
            if len(set(amb)) != len(amb):
                erro("ci.ambientes: há ambiente repetido.")

    infra = perfil.get("infra")
    if infra is not None:
        if not isinstance(infra, dict):
            erro("infra: deve ser objeto.")
        else:
            if "nuvem" in infra and infra["nuvem"] not in NUVENS:
                erro(f"infra.nuvem: '{infra['nuvem']}' inválida ({', '.join(sorted(NUVENS))}).")
            for e in infra.get("execucao") or []:
                if e not in EXECUCOES:
                    erro(f"infra.execucao: '{e}' inválida ({', '.join(sorted(EXECUCOES))}).")
            for c in ("iac", "registro", "observabilidade"):
                if c in infra and not isinstance(infra[c], str):
                    erro(f"infra.{c}: deve ser texto.")
    if isinstance(stacks, list):
        execucao = (infra or {}).get("execucao") or [] if isinstance(infra, dict) else []
        for s, e in INFRA_EXIGE.items():
            if s in stacks and e not in execucao:
                aviso(f"stacks: '{s}' declarada, mas infra.execucao não inclui '{e}'.")
        if "terraform" in stacks and not (isinstance(infra, dict) and infra.get("iac")):
            aviso("stacks: 'terraform' declarada sem infra.iac (pasta da infraestrutura como código).")
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
        f"CI: {obter(perfil, 'ci.provedor', 'nenhum')}" + (f" ({' → '.join(obter(perfil, 'ci.ambientes'))})" if obter(perfil, "ci.ambientes") else ""),
        f"Infra: {obter(perfil, 'infra.nuvem', '-')}" + (f", {', '.join(obter(perfil, 'infra.execucao'))}" if obter(perfil, "infra.execucao") else ""),
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
        print("Sem .claude/projeto.json a partir deste diretório. Rode a skill iniciar (/fluxo:iniciar).")
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
