"""Garante um JWT válido para validar a aplicação local, sem imprimir o token (login de homologação do projeto).

Uso: python -I token_login.py [--forcar]

Perfil: validacao.token.config (JSON local, não versionado, com loginUrl, loginCertSha1 e username)
        validacao.token.arquivo (onde o token é gravado, ex.: .claude/local/token.txt)
Saída: uma linha com status e expiração. Código 0 = token ok; 2 = sem acesso ao login (VPN); 3 = certificado diferente.

O login de homologação usa certificado autoassinado e vencido, que nenhuma cadeia de CA valida. Em vez de desligar a
verificação, o certificado é fixado (pinning): o login só é enviado se o servidor apresentar exatamente o certificado
cuja impressão SHA-1 está em loginCertSha1.
"""
import base64
import datetime
import hashlib
import http.client
import json
import os
import socket
import ssl
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfil as perfil_mod  # noqa: E402


class CertificadoDiferente(Exception):
    pass


def expiracao(token):
    try:
        p = token.split(".")[1]
        p += "=" * (-len(p) % 4)
        return datetime.datetime.fromtimestamp(json.loads(base64.urlsafe_b64decode(p))["exp"], datetime.UTC)
    except Exception:
        return None


class ConexaoFixada(http.client.HTTPSConnection):
    """HTTPS que só segue se o certificado do servidor tiver a impressão esperada."""

    def __init__(self, host, port, sha1, timeout):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE  # a confiança vem do pinning abaixo, não da cadeia de CA
        super().__init__(host, port, context=ctx, timeout=timeout)
        self._sha1 = sha1.replace(":", "").lower()

    def connect(self):
        super().connect()
        recebido = hashlib.sha1(self.sock.getpeercert(binary_form=True)).hexdigest()
        if recebido != self._sha1:
            self.close()
            raise CertificadoDiferente(recebido)


def gerar(cfg, anterior):
    url = urllib.parse.urlparse(cfg["loginUrl"])
    con = ConexaoFixada(url.hostname, url.port or 443, cfg["loginCertSha1"], 20)
    cabecalhos = {"Content-Type": "application/json"}
    if anterior:
        cabecalhos["Authorization"] = f"Bearer {anterior}"
    con.request("POST", url.path, body=json.dumps({"username": cfg["username"]}), headers=cabecalhos)
    r = con.getresponse()
    corpo = json.loads(r.read().decode("utf-8") or "{}")
    token = (corpo.get("token") or "").removeprefix("Bearer ").strip()
    if not token:
        raise RuntimeError(f"login sem token: HTTP {r.status}, mensagem={corpo.get('mensagem')!r}")
    return token


def main():
    raiz, perfil = perfil_mod.carregar()
    arq_cfg = perfil_mod.obter(perfil, "validacao.token.config")
    arq_token = perfil_mod.obter(perfil, "validacao.token.arquivo")
    if not (raiz and arq_cfg and arq_token):
        sys.exit("perfil sem validacao.token.config/arquivo.")
    with open(os.path.join(raiz, arq_cfg), encoding="utf-8") as f:
        cfg = json.load(f)
    caminho = os.path.join(raiz, arq_token)
    atual = None
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            atual = f.read().strip()
    exp = expiracao(atual) if atual else None
    margem = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=30)
    if atual and exp and exp > margem and "--forcar" not in sys.argv:
        print(f"token ok (existente), expira {exp:%Y-%m-%d %H:%M} UTC")
        return
    try:
        atual = gerar(cfg, atual)
    except CertificadoDiferente as e:
        print(f"CERTIFICADO DIFERENTE do fixado (sha1 {e}). Login não enviado; confirme com o time antes de atualizar loginCertSha1.")
        sys.exit(3)
    except (OSError, socket.timeout) as e:
        print(f"SEM ACESSO AO LOGIN ({type(e).__name__}). Conecte a VPN e rode de novo.")
        sys.exit(2)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(atual)
    print(f"token ok (novo), expira {expiracao(atual):%Y-%m-%d %H:%M} UTC")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
