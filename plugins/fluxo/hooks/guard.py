"""Hook PreToolUse do plugin fluxo: bloqueia (exit 2) o que o perfil do projeto proíbe, sem depender da memória do modelo.

Regras (todas lidas de .claude/projeto.json; sem perfil, só a última vale):
1. protecao.textos_proibidos  [{regex, motivo}]  texto na entrada de qualquer ferramenta (ex.: diretório excluído).
2. protecao.diretorios_proibidos [caminho]       ler/editar dentro deles, ou buscar a partir de um diretório que os contém.
3. protecao.gerados [{regex, excecoes, motivo}]   editar à mão arquivo gerado (SDK, proxy, migration gerada).
4. protecao.segredos {arquivos, scripts_permitidos} ler o arquivo de segredo pelo chat (Read ou shell sem o script dono).
5. git.push = "humano" (padrão com perfil)        git push.
6. sempre                                         git commit com segredo (JWT, chave privada, token) nas linhas adicionadas.

Falha ao ler o perfil não bloqueia: o aviso vai para stderr e a ferramenta segue.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import perfil as perfil_mod  # noqa: E402

SEGREDOS = [
    ("um JWT", r"eyJ[\w-]{10,}\.eyJ[\w-]{10,}\.[\w-]{10,}"),
    ("uma chave privada", r"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED |DSA )?PRIVATE KEY-----"),
    ("uma chave de acesso AWS", r"\bAKIA[0-9A-Z]{16}\b"),
    ("um token do GitHub", r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
]
FERRAMENTAS_CAMINHO = ("Read", "Edit", "Write", "NotebookEdit", "Grep", "Glob")


class Bloqueio(Exception):
    pass


def _norm(p):
    return os.path.normcase(os.path.normpath(os.path.abspath(p)))


def _dentro(caminho, base):
    caminho, base = _norm(caminho), _norm(base)
    return caminho == base or caminho.startswith(base.rstrip("\\/") + os.sep)


def comandos_shell(cmd):
    """Trechos que são comandos de fato (separados por ; && || | ou quebra de linha), não texto que os cita."""
    return [s.strip() for s in re.split(r"&&|\|\||[;|\n]", cmd) if s.strip()]


def _eh_git(trecho, sub):
    return re.match(rf"(cd\s+\S+\s+)?git(\s+-C\s+\S+)?(\s+-c\s+\S+)*\s+{sub}\b", trecho) is not None


def segredo_em(texto, extras=()):
    for nome, rx in list(SEGREDOS) + [(e.get("motivo", "um segredo do projeto"), e["regex"]) for e in extras]:
        if re.search(rx, texto):
            return nome
    return None


def diff_staged(raiz):
    r = subprocess.run(["git", "diff", "--cached", "-U0"], cwd=raiz, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return "\n".join(l for l in r.stdout.splitlines() if l.startswith("+") and not l.startswith("+++"))


def verificar(dados, raiz, perfil, obter_diff=diff_staged):
    """Lança Bloqueio(motivo) se a chamada viola o perfil."""
    ferramenta = dados.get("tool_name", "")
    entrada = dados.get("tool_input") or {}
    texto = json.dumps(entrada, ensure_ascii=False)
    protecao = perfil.get("protecao") or {}
    base = raiz or os.getcwd()

    for item in protecao.get("textos_proibidos") or []:
        if re.search(item["regex"], texto, re.I):
            raise Bloqueio(item.get("motivo") or f"texto proibido pelo perfil ({item['regex']}).")

    proibidos = [os.path.join(base, d) for d in protecao.get("diretorios_proibidos") or []]
    if ferramenta in FERRAMENTAS_CAMINHO and proibidos:
        alvo = entrada.get("file_path") or entrada.get("notebook_path") or entrada.get("path") or ""
        alvo_abs = os.path.join(base, alvo) if alvo else base
        for d in proibidos:
            if alvo and _dentro(alvo_abs, d):
                raise Bloqueio(f"{os.path.relpath(d, base)} está na lista de exclusão do projeto.")
            if ferramenta in ("Grep", "Glob") and _dentro(d, alvo_abs) and _norm(d) != _norm(alvo_abs):
                raise Bloqueio(f"busca a partir de um diretório que contém {os.path.relpath(d, base)}; busque dentro do projeto.")

    if ferramenta in ("Edit", "Write", "NotebookEdit"):
        alvo = entrada.get("file_path") or entrada.get("notebook_path") or ""
        for item in protecao.get("gerados") or []:
            if re.search(item["regex"], alvo, re.I) and not any(alvo.endswith(e) for e in item.get("excecoes") or []):
                raise Bloqueio(item.get("motivo") or "arquivo gerado não se edita à mão; altere a fonte e regere.")

    segredos = protecao.get("segredos") or {}
    arquivos = segredos.get("arquivos") or []
    permitidos = segredos.get("scripts_permitidos")
    if ferramenta == "Read":
        alvo = entrada.get("file_path") or ""
        if any(_norm(os.path.join(base, alvo)) == _norm(os.path.join(base, a)) for a in arquivos):
            raise Bloqueio("arquivo de segredo não é lido para o chat; os scripts usam o arquivo diretamente.")

    if ferramenta in ("Bash", "PowerShell"):
        cmd = entrada.get("command", "")
        for a in arquivos:
            # Nome inteiro, como caminho: "server/.env" bloqueia; "process.env", "exemplo.env" e ".env.example" não.
            nome = re.escape(os.path.basename(a))
            if re.search(rf"(?<![\w.-]){nome}(?![\w.-])", cmd) and not (permitidos and re.search(permitidos, cmd)):
                raise Bloqueio(f"{os.path.basename(a)} é segredo; use o script do projeto que o consome.")
        trechos = comandos_shell(cmd)
        if perfil and perfil_mod.obter(perfil, "git.push", "humano") == "humano" and any(_eh_git(t, "push") for t in trechos):
            raise Bloqueio("git push é feito pelo usuário (git.push = humano no perfil).")
        if any(_eh_git(t, "commit") for t in trechos):
            achado = segredo_em(obter_diff(base), protecao.get("segredos_extras") or [])
            if achado:
                raise Bloqueio(f"o diff staged contém {achado}. Remova antes de commitar.")


def main():
    # Claude Code troca JSON em UTF-8; no Windows o padrão do Python é cp1252 (acentos viram lixo ou erro).
    for fluxo in (sys.stdin, sys.stdout, sys.stderr):
        fluxo.reconfigure(encoding="utf-8")
    dados = json.load(sys.stdin)
    inicio = (dados.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    try:
        raiz, perfil = perfil_mod.carregar(inicio)
    except ValueError as e:
        print(f"[fluxo/guard] {e}; proteções do perfil desativadas.", file=sys.stderr)
        raiz, perfil = None, {}
    try:
        verificar(dados, raiz, perfil)
    except Bloqueio as b:
        print(f"Bloqueado pelo guard do plugin fluxo: {b}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
