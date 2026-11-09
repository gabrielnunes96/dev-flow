"""Tarefas de uma demanda (docs/demandas/<slug>/tarefas.json): a fila que o ciclo da task consome.

Uso: python -I plano.py validar  <tarefas.json>
     python -I plano.py proxima  <tarefas.json>            próxima tarefa pronta (JSON); código 1 se não houver
     python -I plano.py prontas  <tarefas.json>            todas as prontas agora (podem rodar em paralelo)
     python -I plano.py marcar   <tarefas.json> <id> <estado> [--commit H] [--wi N] [--nota TEXTO]
     python -I plano.py tabela   <tarefas.json>            tabela markdown (para 03-plano.md, PR e status)
     python -I plano.py resumo   <tarefas.json>            contagem por estado

Estados: a_fazer, andamento, feito, bloqueada. "Pronta" = a_fazer, não protegida e com todas as dependências feitas.
"""
import json
import os
import sys

ESTADOS = ("a_fazer", "andamento", "feito", "bloqueada")


def carregar(arq):
    with open(arq, encoding="utf-8") as f:
        return json.load(f)


def salvar(arq, dados):
    tmp = arq + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, arq)


def validar(dados):
    erros = []
    tarefas = dados.get("tarefas")
    if not isinstance(tarefas, list):
        return ["'tarefas' deve ser uma lista."]
    ids = [t.get("id") for t in tarefas]
    vistos = set()
    for t in tarefas:
        tid = t.get("id")
        if not tid:
            erros.append(f"tarefa sem id: {t.get('titulo')!r}.")
            continue
        if tid in vistos:
            erros.append(f"{tid}: id repetido.")
        vistos.add(tid)
        if not t.get("titulo"):
            erros.append(f"{tid}: sem título.")
        if t.get("estado", "a_fazer") not in ESTADOS:
            erros.append(f"{tid}: estado '{t.get('estado')}' inválido ({', '.join(ESTADOS)}).")
        for d in t.get("depende_de") or []:
            if d not in ids:
                erros.append(f"{tid}: depende de '{d}', que não existe.")
        if not t.get("criterios"):
            erros.append(f"{tid}: sem critérios de aceite (criterios).")
    ciclo = _ciclo(tarefas)
    if ciclo:
        erros.append("dependência circular: " + " -> ".join(ciclo))
    return erros


def _ciclo(tarefas):
    deps = {t.get("id"): list(t.get("depende_de") or []) for t in tarefas if t.get("id")}
    cor = {}

    def visitar(n, caminho):
        cor[n] = 1
        for d in deps.get(n, []):
            if cor.get(d) == 1:
                return caminho + [n, d]
            if d in deps and not cor.get(d):
                achado = visitar(d, caminho + [n])
                if achado:
                    return achado
        cor[n] = 2
        return None

    for n in deps:
        if not cor.get(n):
            achado = visitar(n, [])
            if achado:
                return achado[achado.index(achado[-1]):]
    return None


def prontas(dados):
    por_id = {t["id"]: t for t in dados["tarefas"]}
    return [
        t
        for t in dados["tarefas"]
        if t.get("estado", "a_fazer") == "a_fazer"
        and not t.get("protegida")
        and all(por_id.get(d, {}).get("estado") == "feito" for d in t.get("depende_de") or [])
    ]


def motivo_sem_proxima(dados):
    estados = [t.get("estado", "a_fazer") for t in dados["tarefas"]]
    if all(e == "feito" or t.get("protegida") for e, t in zip(estados, dados["tarefas"])):
        return "fila concluída"
    if "andamento" in estados:
        return "há tarefa em andamento; termine-a antes"
    return "tarefas restantes estão bloqueadas, protegidas ou esperando dependências"


def marcar(dados, tid, estado, commit=None, wi=None, nota=None):
    if estado not in ESTADOS:
        raise ValueError(f"estado inválido: {estado}")
    for t in dados["tarefas"]:
        if t.get("id") == tid:
            if t.get("protegida"):
                raise ValueError(f"{tid} é protegida (controlada pelo usuário).")
            t["estado"] = estado
            if commit:
                t["commit"] = commit
            if wi:
                t["wi"] = int(wi) if str(wi).isdigit() else wi
            if nota:
                t.setdefault("notas", []).append(nota)
            return t
    raise ValueError(f"tarefa {tid} não encontrada.")


def tabela(dados):
    linhas = ["| ID | Tarefa | Stack | Depende de | Estado | WI | Commit |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for t in dados["tarefas"]:
        linhas.append(
            "| {id} | {titulo} | {stack} | {deps} | {estado} | {wi} | {commit} |".format(
                id=t["id"],
                titulo=t.get("titulo", "").replace("|", "\\|"),
                stack=t.get("stack", ""),
                deps=", ".join(t.get("depende_de") or []) or "—",
                estado=t.get("estado", "a_fazer") + (" (protegida)" if t.get("protegida") else ""),
                wi=t.get("wi") or "—",
                commit=t.get("commit") or "—",
            )
        )
    return "\n".join(linhas)


def resumo(dados):
    contagem = {e: 0 for e in ESTADOS}
    for t in dados["tarefas"]:
        contagem[t.get("estado", "a_fazer")] = contagem.get(t.get("estado", "a_fazer"), 0) + 1
    total = len(dados["tarefas"])
    return f"{contagem['feito']}/{total} feitas, {contagem['andamento']} em andamento, {contagem['a_fazer']} a fazer, {contagem['bloqueada']} bloqueadas"


def _opcao(argv, nome):
    if nome in argv:
        i = argv.index(nome)
        if i + 1 < len(argv):
            return argv[i + 1]
    return None


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    acao, arq = argv[1], argv[2]
    dados = carregar(arq)
    if acao == "validar":
        erros = validar(dados)
        print("\n".join(erros) if erros else "tarefas ok: " + resumo(dados))
        return 1 if erros else 0
    if acao == "proxima":
        p = prontas(dados)
        if not p:
            print(motivo_sem_proxima(dados))
            return 1
        print(json.dumps(p[0], ensure_ascii=False, indent=2))
        return 0
    if acao == "prontas":
        print(json.dumps(prontas(dados), ensure_ascii=False, indent=2))
        return 0
    if acao == "marcar":
        if len(argv) < 5:
            sys.exit(__doc__)
        try:
            t = marcar(dados, argv[3], argv[4], _opcao(argv, "--commit"), _opcao(argv, "--wi"), _opcao(argv, "--nota"))
        except ValueError as e:
            print(e)
            return 1
        salvar(arq, dados)
        print(f"{t['id']} -> {t['estado']}")
        return 0
    if acao == "tabela":
        print(tabela(dados))
        return 0
    if acao == "resumo":
        print(resumo(dados))
        return 0
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
