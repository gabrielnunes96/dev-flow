"""Hook SessionStart do plugin fluxo: injeta no contexto um resumo curto do projeto e da demanda ativa.

Sai em silêncio se a pasta não tiver .claude/projeto.json e não for um repositório git (ex.: sessão fora de projeto).
"""
import glob
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(AQUI, "..", "scripts"))
sys.path.insert(0, SCRIPTS)
import perfil as perfil_mod  # noqa: E402
import plano  # noqa: E402


def demanda_ativa(raiz, docs):
    """tarefas.json mais recente que ainda tem tarefa não feita."""
    arquivos = sorted(glob.glob(os.path.join(raiz, docs, "*", "tarefas.json")), key=os.path.getmtime, reverse=True)
    for arq in arquivos:
        try:
            dados = plano.carregar(arq)
        except (OSError, ValueError):
            continue
        if any(t.get("estado") != "feito" and not t.get("protegida") for t in dados.get("tarefas", [])):
            return arq, dados
    return None, None


def main():
    try:
        dados = json.load(sys.stdin)
    except ValueError:
        dados = {}
    inicio = dados.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        raiz, perfil = perfil_mod.carregar(inicio)
    except ValueError as e:
        print(f"[fluxo] {e}")
        return
    if not raiz:
        if os.path.isdir(os.path.join(inicio, ".git")):
            print("[fluxo] Projeto sem .claude/projeto.json; /fluxo:iniciar cria o perfil.")
        return
    linhas = [
        f"[fluxo] Projeto {perfil.get('nome')} ({', '.join(perfil.get('stacks') or [])}); perfil em {os.path.join(raiz, perfil_mod.ARQUIVO)}.",
        f"[fluxo] Scripts do plugin (rodar com python -I): {SCRIPTS}",
    ]
    arq, dados_plano = demanda_ativa(raiz, perfil.get("docs", "docs/demandas"))
    if arq:
        p = plano.prontas(dados_plano)
        prox = f"; próxima pronta: {p[0]['id']} {p[0].get('titulo')}" if p else ""
        linhas.append(f"[fluxo] Demanda ativa: {os.path.relpath(os.path.dirname(arq), raiz)} ({plano.resumo(dados_plano)}{prox}).")
    print("\n".join(linhas))


if __name__ == "__main__":
    for fluxo in (sys.stdin, sys.stdout, sys.stderr):
        fluxo.reconfigure(encoding="utf-8")
    main()
