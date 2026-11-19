#!/usr/bin/env python3
"""Mantém o conhecimento volátil das stacks (plugins/stack-*/referencias/atual.md) em dia.

Modos:
  --verificar      offline: estrutura dos atual.md e revisão humana vencida (--max-dias, padrão 120;
                   0 = só estrutura, para o CI de PR não travar com o tempo).
                   Saída 0 ok, 1 problema.
  (padrão)         online: busca https://endoflife.date/api/<produto>.json para os produtos de cada stack,
                   regrava o bloco de versões (só se mudou), compara com o bloco anterior e varre plugins/
                   por versões citadas que já estão sem suporte. Saída 0 sem achados, 2 com achados, 1 erro.

Opções do modo online:
  --relatorio ARQ  grava o relatório em Markdown (também vai para a saída padrão)
  --sem-gravar     não altera os atual.md
  --fonte-dir DIR  lê DIR/<produto>.json em vez da rede (testes e uso offline)
  --stack X        só essas stacks (repetível)
  --hoje AAAA-MM-DD  data de referência (testes)

Formato de atual.md (ver docs/novo-plugin-de-stack.md):
  <!-- dev-flow:conhecimento revisado_em=AAAA-MM-DD produtos=prod1,prod2 -->
  ## Fontes oficiais  (ao menos um link)
  ## Versões         <!-- versoes:inicio --> ... <!-- versoes:fim -->
  ## Mudanças a observar
"""
import argparse
import datetime as dt
import glob
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.request

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PLUGINS = os.path.join(RAIZ, "plugins")
API = "https://endoflife.date/api/{}.json"
META = re.compile(r"<!--\s*dev-flow:conhecimento\s+(.*?)-->")
BLOCO = re.compile(r"(<!-- versoes:inicio -->)(.*?)(<!-- versoes:fim -->)", re.S)
SECOES = ("## Fontes oficiais", "## Versões", "## Mudanças a observar")
SEM_SUPORTE_MOSTRADOS = 2
EXTENSOES = (".md", ".yml", ".yaml", ".json", ".tf", ".txt", ".toml", ".cs", ".py", ".js", ".ts", ".css", ".html")

# Como cada produto aparece citado em texto, YAML ou imagem de container. O grupo 1 é o ciclo.
PADROES = {
    "nodejs": [r"\bNode(?:\.js)?\s+v?(\d{2})\b", r"\bnode:(\d{2})\b", r"node-version:\s*['\"]?(\d{2})\b"],
    "python": [r"\b[Pp]ython\s+(3\.\d+)\b", r"\bpython:(3\.\d+)\b", r"python-version:\s*['\"]?(3\.\d+)"],
    "dotnet": [r"\.NET\s+(\d{1,2}(?:\.0)?)\b", r"dotnet/(?:sdk|aspnet|runtime(?:-deps)?):(\d{1,2}\.\d)", r"\bDOTNET(?:_VERSION)?=(\d{1,2}\.\d)"],
    "eclipse-temurin": [r"\b(?:Java|JDK)\s+(\d{2})\b", r"\beclipse-temurin:(\d{2})\b"],
    "spring-boot": [r"\bSpring Boot\s+(\d\.\d+)\b"],
    "go": [r"\bGo\s+(1\.\d+)\b", r"\bgolang:(1\.\d+)\b", r"^go\s+(1\.\d+)"],
    "postgresql": [r"\bPostgre(?:SQL|s)\s+(\d{2}|9\.\d)\b", r"\bpostgres:(\d{2}|9\.\d)\b"],
    "mysql": [r"\bMySQL\s+(\d\.\d)\b", r"\bmysql:(\d\.\d)\b"],
    "mariadb": [r"\bMariaDB\s+(\d{2}\.\d+)\b", r"\bmariadb:(\d{2}\.\d+)\b"],
    "mongodb": [r"\bMongoDB\s+(\d\.\d)\b", r"\bmongo:(\d\.\d)\b"],
    "redis": [r"\bRedis\s+(\d\.\d)\b", r"\bredis:(\d\.\d)\b"],
    "kubernetes": [r"\bKubernetes\s+(1\.\d+)\b"],
    "terraform": [r"\bTerraform\s+(1\.\d+)\b"],
    "react": [r"\bReact\s+(\d{2})\b"],
    "angular": [r"\bAngular\s+(\d{2})\b"],
    "vue": [r"\bVue\s+(\d)\b"],
    "mssqlserver": [r"\bSQL Server\s+(20\d\d)\b"],
    "django": [r"\bDjango\s+(\d\.\d)\b"],
    "docker-engine": [r"\bDocker (?:Engine\s+)?(\d{2}\.\d+)\b", r"\bdocker:(\d{2}\.\d+)"],
}


# Citação histórica ("antes do Go 1.22", "desde o Python 3.10") não é recomendação de versão.
HISTORICO = re.compile(r"\b(?:antes|depois|desde|a partir|até|before|since|prior to|after)\b[\w\s.]{0,4}$", re.I)


class Erro(Exception):
    pass


# ---------- leitura dos atual.md ----------

def arquivos_atual(stacks=None):
    saida = {}
    for arq in sorted(glob.glob(os.path.join(PLUGINS, "stack-*", "referencias", "atual.md"))):
        stack = os.path.basename(os.path.dirname(os.path.dirname(arq)))[len("stack-"):]
        if not stacks or stack in stacks:
            saida[stack] = arq
    return saida


def ler(arq):
    with open(arq, encoding="utf-8", newline="") as f:
        texto = f.read()
    m = META.search(texto)
    meta = dict(re.findall(r"(\w+)=(\S+)", m.group(1))) if m else {}
    produtos = [p for p in meta.get("produtos", "").split(",") if p]
    revisado = None
    try:
        revisado = dt.date.fromisoformat(meta.get("revisado_em", ""))
    except ValueError:
        pass
    fontes = ""
    if "## Fontes oficiais" in texto:
        fontes = texto.split("## Fontes oficiais", 1)[1].split("\n## ", 1)[0]
    bloco = BLOCO.search(texto)
    return {
        "texto": texto,
        "tem_meta": bool(m),
        "produtos": produtos,
        "revisado_em": revisado,
        "n_fontes": len(re.findall(r"https?://", fontes)),
        "bloco": bloco.group(2) if bloco else None,
        "secoes": [s for s in SECOES if s in texto],
    }


def linhas_da_tabela(bloco):
    """{(produto, ciclo): situacao} a partir da tabela gerada."""
    linhas = {}
    for l in (bloco or "").splitlines():
        cel = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cel) >= 3 and cel[0] not in ("Produto", "---", "") and not cel[0].startswith("-"):
            linhas[(cel[0], cel[1])] = cel[2]
    return linhas


# ---------- verificação offline ----------

def verificar(hoje, max_dias=120, stacks=None):
    problemas = []
    atuais = arquivos_atual(stacks)
    pastas = {os.path.basename(p)[len("stack-"):] for p in glob.glob(os.path.join(PLUGINS, "stack-*"))}
    for stack in sorted((set(stacks) if stacks else pastas) - set(atuais)):
        problemas.append(f"stack-{stack}: falta referencias/atual.md")
    for stack, arq in atuais.items():
        d = ler(arq)
        rel = os.path.relpath(arq, RAIZ)
        if not d["tem_meta"] or not d["produtos"]:
            problemas.append(f"{rel}: falta o comentário dev-flow:conhecimento com produtos=")
        if d["revisado_em"] is None:
            problemas.append(f"{rel}: revisado_em ausente ou inválido (AAAA-MM-DD)")
        elif max_dias > 0 and (hoje - d["revisado_em"]).days > max_dias:
            problemas.append(f"{rel}: revisão vencida ({d['revisado_em']}, mais de {max_dias} dias)")
        for s in SECOES:
            if s not in d["secoes"]:
                problemas.append(f"{rel}: falta a seção '{s}'")
        if d["n_fontes"] < 1:
            problemas.append(f"{rel}: '## Fontes oficiais' sem link")
        if d["bloco"] is None:
            problemas.append(f"{rel}: falta o bloco <!-- versoes:inicio --> ... <!-- versoes:fim -->")
    return problemas


# ---------- dados de versão ----------

def _data(v):
    if isinstance(v, str):
        try:
            return dt.date.fromisoformat(v[:10])
        except ValueError:
            return None
    return None


def sem_suporte(ciclo, hoje):
    eol = ciclo.get("eol")
    if eol is True:
        return True
    d = _data(eol)
    return bool(d and d <= hoje)


def situacao(ciclo, hoje):
    if sem_suporte(ciclo, hoje):
        return "sem suporte"
    lts = ciclo.get("lts")
    if lts is True or (_data(lts) and _data(lts) <= hoje):
        return "LTS"
    suporte = _data(ciclo.get("support"))
    if suporte and suporte <= hoje:
        return "suporte ativo encerrado"  # só correções de segurança até o fim, ou nenhuma se não há fim declarado
    return "suportado"


def normalizar(versao):
    """'8.0' e '8' são o mesmo ciclo; '17.0' (SQL Server) idem."""
    return re.sub(r"\.0$", "", str(versao))


def nomes_do_ciclo(ciclo):
    """Como um ciclo pode aparecer citado: o próprio ciclo e, se houver, o ano do releaseLabel (SQL Server 2022)."""
    nomes = {normalizar(ciclo["cycle"])}
    ano = re.match(r"(20\d\d)\b", str(ciclo.get("releaseLabel") or ""))
    if ano:
        nomes.add(ano.group(1))
    return nomes


def _texto(v):
    if v is True:
        return "sim"
    if v in (False, None, ""):
        return "—"
    return str(v).replace("|", "/")


def buscar(produto, fonte_dir=None):
    if fonte_dir:
        arq = os.path.join(fonte_dir, f"{produto}.json")
        if not os.path.isfile(arq):
            raise Erro(f"sem {produto}.json em {fonte_dir}")
        try:
            with open(arq, encoding="utf-8") as f:
                dados = json.load(f)
        except ValueError as e:
            raise Erro(f"{produto}: JSON inválido em {arq}: {e}") from e
    else:
        req = urllib.request.Request(API.format(produto), headers={"User-Agent": "dev-flow-conhecimento"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                dados = json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError) as e:
            raise Erro(f"{produto}: {e}") from e
    if not isinstance(dados, list) or not all(isinstance(c, dict) and "cycle" in c for c in dados):
        raise Erro(f"{produto}: resposta inesperada")
    return dados


def tabela(dados_por_produto, hoje):
    linhas = ["| Produto | Ciclo | Situação | Lançado | Suporte ativo até | Fim de suporte | Última |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for produto, ciclos in dados_por_produto.items():
        vivos = [c for c in ciclos if not sem_suporte(c, hoje)]
        mortos = [c for c in ciclos if sem_suporte(c, hoje)][:SEM_SUPORTE_MOSTRADOS]
        for c in vivos + mortos:
            linhas.append("| " + " | ".join([produto, _texto(c["cycle"]), situacao(c, hoje), _texto(c.get("releaseDate")),
                                             _texto(c.get("support")), _texto(c.get("eol")), _texto(c.get("latest"))]) + " |")
    return linhas


def linhas_cheias(bloco):
    """Linhas da tabela inteiras (para decidir se regrava); ignora a linha 'Gerado em'."""
    return [l.strip() for l in (bloco or "").splitlines() if l.strip().startswith("|")]


def gravar_atomico(arq, texto):
    tmp = arq + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(texto)
    os.replace(tmp, arq)


def novo_bloco(dados_por_produto, hoje):
    return ("\n" + f"Gerado em {hoje.isoformat()} por `scripts/atualizar_conhecimento.py` a partir de endoflife.date "
            f"(ciclos com suporte e os {SEM_SUPORTE_MOSTRADOS} últimos sem suporte). Não editar à mão.\n\n"
            + "\n".join(tabela(dados_por_produto, hoje)) + "\n")


# ---------- comparação e varredura ----------

def comparar(anteriores, dados_por_produto, hoje):
    achados = []
    for produto, ciclos in dados_por_produto.items():
        antigos = {c: s for (p, c), s in anteriores.items() if p == produto}
        if not antigos:
            continue  # primeira geração: nada a comparar
        for c in ciclos:
            ciclo = str(c["cycle"])
            agora = situacao(c, hoje)
            antes = antigos.get(ciclo)
            if antes is None and agora != "sem suporte":
                achados.append(("novo_ciclo", f"{produto} {ciclo} ({agora})"))
            elif antes is not None and antes != "sem suporte" and agora == "sem suporte":
                achados.append(("fim_de_suporte", f"{produto} {ciclo} saiu de suporte (fim: {_texto(c.get('eol'))})"))
            elif antes in ("LTS", "suportado") and agora == "suporte ativo encerrado":
                achados.append(("fim_de_suporte", f"{produto} {ciclo} encerrou o suporte ativo (fim: {_texto(c.get('eol'))})"))
            elif antes is not None and antes != "LTS" and agora == "LTS":
                achados.append(("novo_lts", f"{produto} {ciclo} virou LTS"))
    return achados


def _arquivos_varridos():
    for raiz, pastas, arquivos in os.walk(PLUGINS):
        pastas[:] = [p for p in pastas if p not in ("__pycache__", "results", "node_modules", "evals")]
        for nome in arquivos:
            if nome.endswith(EXTENSOES) or nome.startswith("Dockerfile") or nome in ("dockerignore", "go.mod"):
                arq = os.path.join(raiz, nome)
                if not (nome == "atual.md" and os.path.basename(raiz) == "referencias"):
                    yield arq


def versoes_sem_suporte(dados_por_produto, hoje):
    mortos = {}
    for produto, ciclos in dados_por_produto.items():
        for c in ciclos:
            if sem_suporte(c, hoje):
                mortos.setdefault(produto, set()).update(nomes_do_ciclo(c))
    achados = []
    if not mortos:
        return achados
    padroes = [(p, re.compile(rx, re.M)) for p in mortos for rx in PADROES.get(p, [])]
    for arq in _arquivos_varridos():
        try:
            with open(arq, encoding="utf-8") as f:
                linhas = f.read().splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for n, linha in enumerate(linhas, 1):
            for produto, rx in padroes:
                for m in rx.finditer(linha):
                    v = m.group(1)
                    if HISTORICO.search(linha[:m.start()]):
                        continue
                    if normalizar(v) in mortos[produto]:
                        achados.append(("versao_sem_suporte",
                                        f"{os.path.relpath(arq, RAIZ)}:{n} cita {produto} {v}, sem suporte"))
    return achados


# ---------- execução online ----------

def levantar(hoje, stacks=None, fonte_dir=None, gravar=True, max_dias=120):
    atuais = arquivos_atual(stacks)
    if not atuais:
        raise Erro("nenhum plugins/stack-*/referencias/atual.md encontrado")
    achados, cache, todos = [], {}, {}
    for stack, arq in atuais.items():
        d = ler(arq)
        rel = os.path.relpath(arq, RAIZ)
        if d["revisado_em"] and max_dias > 0 and (hoje - d["revisado_em"]).days > max_dias:
            achados.append(("revisao_vencida", f"{rel}: revisado em {d['revisado_em']}"))
        if not d["produtos"] or d["bloco"] is None:
            achados.append(("estrutura", f"{rel}: sem produtos= ou sem bloco de versões (rode --verificar)"))
            continue
        dados, falhou = {}, False
        for produto in d["produtos"]:
            if produto not in cache:
                try:
                    cache[produto] = buscar(produto, fonte_dir)
                except Erro as e:
                    cache[produto] = e
            if isinstance(cache[produto], Erro):
                achados.append(("falha_fonte", f"stack-{stack}: {cache[produto]} (arquivo não alterado)"))
                falhou = True
            else:
                dados[produto] = cache[produto]
        todos.update(dados)
        if falhou or not dados:
            continue
        achados += [(t, f"stack-{stack}: {m}") for t, m in comparar(linhas_da_tabela(d["bloco"]), dados, hoje)]
        bloco = novo_bloco(dados, hoje)
        if gravar and linhas_cheias(bloco) != linhas_cheias(d["bloco"]):
            if "\r\n" in d["texto"]:
                bloco = bloco.replace("\n", "\r\n")
            texto = BLOCO.sub(lambda m: m.group(1) + bloco + m.group(3), d["texto"], count=1)
            gravar_atomico(arq, texto)
    if not todos and any(t == "falha_fonte" for t, _ in achados):
        raise Erro("nenhum produto consultado: " + "; ".join(m for t, m in achados if t == "falha_fonte"))
    achados += versoes_sem_suporte(todos, hoje)
    return achados


TITULOS = {
    "novo_ciclo": "Ciclos novos",
    "novo_lts": "Novos LTS",
    "fim_de_suporte": "Saíram de suporte",
    "versao_sem_suporte": "Versões sem suporte citadas nos plugins",
    "revisao_vencida": "Curadoria com revisão vencida",
    "falha_fonte": "Falhas ao consultar a fonte",
    "estrutura": "Arquivos fora do formato",
}


def relatorio(achados, hoje):
    linhas = [f"# Revisão de conhecimento das stacks — {hoje.isoformat()}", ""]
    if not achados:
        return "\n".join(linhas + ["Sem achados: versões em dia e nenhuma versão sem suporte citada.", ""])
    for tipo, titulo in TITULOS.items():
        itens = [m for t, m in achados if t == tipo]
        if itens:
            linhas += [f"## {titulo} ({len(itens)})", ""] + [f"- {m}" for m in itens] + [""]
    linhas += ["Próximo passo: skill `atualizar-conhecimento` (curadoria das mudanças, branch e PR para aprovação).", ""]
    return "\n".join(linhas)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verificar", action="store_true")
    ap.add_argument("--max-dias", type=int, default=120)
    ap.add_argument("--relatorio")
    ap.add_argument("--sem-gravar", action="store_true")
    ap.add_argument("--fonte-dir")
    ap.add_argument("--stack", action="append")
    ap.add_argument("--hoje")
    args = ap.parse_args(argv)
    try:
        hoje = dt.date.fromisoformat(args.hoje) if args.hoje else dt.date.today()
    except ValueError:
        print(f"erro: --hoje inválido: {args.hoje} (AAAA-MM-DD)", file=sys.stderr)
        return 1
    if args.verificar:
        problemas = verificar(hoje, args.max_dias, args.stack)
        for p in problemas:
            print(p)
        print("conhecimento ok" if not problemas else f"{len(problemas)} problema(s)")
        return 1 if problemas else 0
    try:
        achados = levantar(hoje, args.stack, args.fonte_dir, not args.sem_gravar, args.max_dias)
    except Erro as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    texto = relatorio(achados, hoje)
    print(texto)
    if args.relatorio:
        with open(args.relatorio, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
    return 2 if achados else 0


if __name__ == "__main__":
    for fluxo in (sys.stdout, sys.stderr):
        fluxo.reconfigure(encoding="utf-8")
    sys.exit(main())
