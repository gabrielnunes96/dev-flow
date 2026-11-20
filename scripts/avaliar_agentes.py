#!/usr/bin/env python3
"""Roda a suíte de comportamento dos especialistas (plugins/*/evals/<agente>/<caso>/) com qualquer agente de linha de comando.

Os casos usam o formato do `claude plugin eval` (prompt.md + graders/*.md), então no Claude Code também dá para rodar
`claude plugin eval plugins/fluxo`. Este executor é o caminho para os outros hosts (Cursor, Codex, qualquer CLI):

  python -I scripts/avaliar_agentes.py --comando "claude -p"
  python -I scripts/avaliar_agentes.py --comando "cursor-agent -p --output-format text" --juiz "cursor-agent -p"
  python -I scripts/avaliar_agentes.py --comando "codex exec -" --caso "revisor/*"
  python -I scripts/avaliar_agentes.py --listar

O prompt enviado é o corpo de plugins/<plugin>/agents/<agente>.md seguido do prompt.md do caso; vai pela entrada
padrão, ou por arquivo quando o comando tem `{prompt_arquivo}`. Verificações:
  regex  aplicada à resposta (pattern, flags=i, match=contains|not_contains|count:N)
  llm    só com --juiz: o juiz recebe o critério e a resposta e responde PASS ou FAIL na primeira linha
  outras (tool_used, file_exists...) dependem do host: "não avaliado", não reprovam.

Saída 0 se todo caso passou em todas as --execucoes; 1 se algum reprovou, deu erro ou ficou sem nenhuma
verificação avaliada (caso só com verificação llm exige --juiz). O comando roda numa pasta temporária vazia,
para o agente não ler nem alterar o repositório de quem roda.
Cada execução é uma chamada real ao modelo do comando escolhido (custo de quem roda).
"""
import argparse
import fnmatch
import glob
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PLUGINS = os.path.join(RAIZ, "plugins")
FM = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.S)


class Erro(Exception):
    pass


def frontmatter(texto):
    """(campos, corpo). YAML simples: chave: valor, listas [a, b], strings entre aspas."""
    texto = texto.lstrip("\ufeff")
    m = FM.match(texto)
    if not m:
        return {}, texto
    campos = {}
    for linha in m.group(1).splitlines():
        if ":" not in linha or linha.startswith((" ", "\t", "#")):
            continue
        chave, valor = linha.split(":", 1)
        valor = valor.strip()
        if valor.startswith("[") and valor.endswith("]"):
            valor = [v.strip().strip("'\"") for v in valor[1:-1].split(",") if v.strip()]
        elif len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "'\"":
            valor = valor[1:-1]
        campos[chave.strip()] = valor
    return campos, texto[m.end():].strip()


def _ler(arq):
    with open(arq, encoding="utf-8") as f:
        return f.read()


def casos(plugins=None, filtro=None):
    saida = []
    for prompt in sorted(glob.glob(os.path.join(PLUGINS, "*", "evals", "**", "prompt.md"), recursive=True)):
        pasta = os.path.dirname(prompt)
        plugin = os.path.relpath(pasta, PLUGINS).split(os.sep)[0]
        agente = os.path.basename(os.path.dirname(pasta))
        nome = f"{agente}/{os.path.basename(pasta)}"
        if plugins and plugin not in plugins:
            continue
        if filtro and not fnmatch.fnmatch(nome, filtro):
            continue
        campos, corpo = frontmatter(_ler(prompt))
        graders = []
        for g in sorted(glob.glob(os.path.join(pasta, "graders", "*.md"))):
            gc, gcorpo = frontmatter(_ler(g))
            graders.append({"nome": os.path.splitext(os.path.basename(g))[0], "campos": gc, "criterio": gcorpo})
        saida.append({"nome": nome, "plugin": plugin, "agente": agente, "pasta": pasta, "campos": campos,
                      "prompt": corpo, "graders": graders,
                      "arquivo_agente": os.path.join(PLUGINS, plugin, "agents", f"{agente}.md")})
    return saida


def montar_prompt(caso):
    if not os.path.isfile(caso["arquivo_agente"]):
        raise Erro(f"{caso['nome']}: especialista sem arquivo {os.path.relpath(caso['arquivo_agente'], RAIZ)}")
    _, instrucoes = frontmatter(_ler(caso["arquivo_agente"]))
    return ("Você é o especialista descrito abaixo. Siga as instruções dele.\n\n" + instrucoes
            + "\n\n---\n\n" + caso["prompt"] + "\n")


def dividir(comando):
    """Argumentos do comando; no Windows tira as aspas das pontas e acha .cmd/.exe no PATH (CLIs do npm)."""
    if os.name == "nt":
        args = [a[1:-1] if len(a) >= 2 and a[0] == a[-1] and a[0] in "'\"" else a
                for a in shlex.split(comando, posix=False)]
    else:
        args = shlex.split(comando)
    if not args:
        raise Erro("comando vazio")
    args[0] = shutil.which(args[0]) or args[0]
    return args


def executar(comando, prompt, timeout):
    args = dividir(comando)
    arq = None
    pasta = tempfile.mkdtemp(prefix="avaliacao-")
    try:
        if any("{prompt_arquivo}" in a for a in args):
            fd, arq = tempfile.mkstemp(prefix="prompt-", suffix=".md")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(prompt)
            args = [a.replace("{prompt_arquivo}", arq) for a in args]
            entrada = {"stdin": subprocess.DEVNULL}
        else:
            entrada = {"input": prompt}
        r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, cwd=pasta, **entrada)
    except FileNotFoundError as e:
        raise Erro(f"comando não encontrado: {args[0]}") from e
    except PermissionError as e:
        raise Erro(f"sem permissão para executar: {args[0]}") from e
    except subprocess.TimeoutExpired as e:
        raise Erro(f"tempo esgotado ({timeout} s)") from e
    finally:
        if arq:
            os.remove(arq)
        shutil.rmtree(pasta, ignore_errors=True)
    if r.returncode != 0:
        detalhe = (r.stderr.strip() or r.stdout.strip())[-300:]
        raise Erro(f"comando saiu com {r.returncode}: {detalhe}")
    return r.stdout


def avaliar_regex(campos, resposta):
    flags = re.I if "i" in str(campos.get("flags", "")) else 0
    n = len(re.findall(campos["pattern"], resposta, flags))
    match = str(campos.get("match", "contains"))
    if match == "contains":
        return n > 0
    if match == "not_contains":
        return n == 0
    if match.startswith("count:"):
        return n == int(match.split(":", 1)[1])
    raise Erro(f"match desconhecido: {match}")


def avaliar(grader, resposta, juiz, timeout):
    """True/False, ou None quando não avaliado."""
    campos = grader["campos"]
    alvo = campos.get("target", "last_message")
    if alvo != "last_message":
        return None
    tipo = campos.get("type")
    if tipo == "regex":
        return avaliar_regex(campos, resposta)
    if tipo == "llm" and juiz:
        pergunta = ("Você é um avaliador. Critério:\n\n" + (campos.get("criteria") or grader["criterio"])
                    + "\n\nResposta avaliada:\n\n<<<\n" + resposta + "\n>>>\n\nResponda só PASS ou FAIL na primeira linha.")
        veredito = re.search(r"\b(PASS|FAIL)\b", executar(juiz, pergunta, timeout).upper())
        if not veredito:
            raise Erro("o juiz não respondeu PASS nem FAIL")
        return veredito.group(1) == "PASS"
    return None


def rodar(lista, comando, juiz=None, execucoes=1, saida=print):
    resultados, falhou = [], False
    for caso in lista:
        aprovadas, avaliadas, detalhes, erro = 0, 0, [], None
        try:
            try:
                timeout = int(caso["campos"].get("timeout_seconds") or 300)
            except ValueError as e:
                raise Erro("timeout_seconds não numérico") from e
            prompt = montar_prompt(caso)
            for _ in range(execucoes):
                resposta = executar(comando, prompt, timeout)
                try:
                    notas = {g["nome"]: avaliar(g, resposta, juiz, timeout) for g in caso["graders"]}
                except (KeyError, re.error, ValueError) as e:
                    raise Erro(f"verificação mal formada: {e}") from e
                detalhes.append(notas)
                validas = [v for v in notas.values() if v is not None]
                if validas:
                    avaliadas += 1
                    aprovadas += all(validas)
        except Erro as e:
            erro = str(e)
        if erro:
            situacao = "ERRO"
        elif not avaliadas:
            situacao = "NÃO AVALIADO"
        else:
            situacao = "OK" if aprovadas == avaliadas == execucoes else "REPROVADO"
        falhou |= situacao != "OK"
        resultados.append({"caso": caso["nome"], "situacao": situacao, "aprovadas": aprovadas, "avaliadas": avaliadas,
                           "verificacoes": detalhes, "erro": erro})
        saida(f"{situacao:13} {caso['nome']} ({aprovadas}/{avaliadas})" + (f" — {erro}" if erro else ""))
    return resultados, falhou


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--comando", help='agente a avaliar, ex.: "claude -p"')
    ap.add_argument("--juiz", help="comando que julga as verificações llm (PASS/FAIL)")
    ap.add_argument("--caso", help="filtro agente/caso (glob), ex.: 'revisor/*'")
    ap.add_argument("--plugin", action="append", help="só estes plugins")
    ap.add_argument("--execucoes", type=int, default=1)
    ap.add_argument("--json", help="grava os resultados neste arquivo")
    ap.add_argument("--listar", action="store_true")
    args = ap.parse_args(argv)
    lista = casos(args.plugin, args.caso)
    if not lista:
        print("nenhum caso encontrado", file=sys.stderr)
        return 1
    if args.listar:
        for c in lista:
            tipos = ", ".join(sorted({g["campos"].get("type", "?") for g in c["graders"]}))
            print(f"{c['nome']}  [{tipos}]  {c['campos'].get('description', '')}")
        return 0
    if not args.comando:
        ap.error("informe --comando (ou --listar)")
    resultados, falhou = rodar(lista, args.comando, args.juiz, args.execucoes)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
    if not args.juiz and any(g["campos"].get("type") == "llm" for c in lista for g in c["graders"]):
        print("aviso: verificações llm não avaliadas (use --juiz); caso sem nenhuma verificação avaliada reprova")
    return 1 if falhou else 0


if __name__ == "__main__":
    for fluxo in (sys.stdout, sys.stderr):
        fluxo.reconfigure(encoding="utf-8")
    sys.exit(main())
