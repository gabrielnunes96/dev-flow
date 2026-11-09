"""Sobe/derruba a aplicação local para validação, conforme a seção "servico" do perfil.

Uso: python -I servico.py subir [--build]   derruba a anterior, (compila), sobe em segundo plano e espera o healthcheck
     python -I servico.py derrubar          encerra os processos da aplicação (necessário antes de compilar no Windows)

Perfil:
  servico.executar     comando (lista de argumentos) que sobe a aplicação, ex.: ["dotnet","run","--no-build","--project","src/Api"]
  servico.healthcheck  URL que responde 200 quando a aplicação está no ar
  servico.processos    nomes de processo para encerrar (curinga * permitido), ex.: ["Acme*"]
  servico.log          arquivo de log (padrão .claude/local/servico.log)
  comandos.build       comando de build usado com --build
"""
import os
import shlex
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfil as perfil_mod  # noqa: E402

WINDOWS = os.name == "nt"


def derrubar(servico):
    for nome in servico.get("processos") or []:
        if WINDOWS:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"Get-Process '{nome}' -ErrorAction SilentlyContinue | Stop-Process -Force"],
                check=False,
            )
        else:
            subprocess.run(["pkill", "-f", nome.replace("*", "")], check=False)
    time.sleep(1)


def build(raiz, comando):
    r = subprocess.run(comando, cwd=raiz, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        saida = r.stdout + r.stderr
        erros = sorted({l.strip() for l in saida.splitlines() if " error " in l.lower() or ": error" in l.lower()}) or saida.splitlines()[-30:]
        sys.exit("build falhou:\n" + "\n".join(erros[:30]))
    print("build ok")


def subir(raiz, perfil, com_build):
    servico = perfil.get("servico") or {}
    if not servico.get("executar") or not servico.get("healthcheck"):
        sys.exit("perfil sem servico.executar/healthcheck.")
    derrubar(servico)
    if com_build:
        cmd = perfil_mod.obter(perfil, "comandos.build")
        if not cmd:
            sys.exit("perfil sem comandos.build.")
        build(raiz, cmd)
    arq_log = os.path.join(raiz, servico.get("log", ".claude/local/servico.log"))
    os.makedirs(os.path.dirname(arq_log), exist_ok=True)
    log = open(arq_log, "w", encoding="utf-8")
    executar = servico["executar"] if isinstance(servico["executar"], list) else shlex.split(servico["executar"])
    flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP if WINDOWS else 0
    subprocess.Popen(executar, cwd=raiz, stdout=log, stderr=subprocess.STDOUT, creationflags=flags, start_new_session=not WINDOWS)
    for _ in range(int(servico.get("espera_segundos", 180)) // 2):
        try:
            with urllib.request.urlopen(servico["healthcheck"], timeout=2) as r:
                if r.status == 200:
                    print("aplicação no ar:", servico["healthcheck"])
                    return
        except Exception:
            time.sleep(2)
    sys.exit(f"healthcheck sem 200; veja {os.path.relpath(arq_log, raiz)}")


def main(argv):
    raiz, perfil = perfil_mod.carregar()
    if not raiz:
        sys.exit("sem .claude/projeto.json.")
    acao = argv[1] if len(argv) > 1 else ""
    if acao == "subir":
        subir(raiz, perfil, "--build" in argv)
    elif acao == "derrubar":
        derrubar(perfil.get("servico") or {})
        print("aplicação derrubada")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv)
