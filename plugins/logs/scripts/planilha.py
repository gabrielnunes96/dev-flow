"""Planilha Excel da análise. Só biblioteca padrão.

A aba Achados é o problema. A aba Níveis é linha do arquivo, saudável ou não.
"""
import io
import re
import zipfile
from xml.sax.saxutils import escape

NIVEL = {
    "error": "Erro",
    "warning": "Aviso",
    "info": "Info",
    "debug": "Debug",
    "outro": "Sem nível",
}
CLASSE = {
    "falso_negativo": "Falso negativo",
    "erro": "Erro",
    "aviso": "Aviso",
    "falso_positivo": "Falso positivo",
}

_TIPOS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet4.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""

_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""

_WB_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>
<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet4.xml"/>
<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""

_WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>
<sheet name="Achados" sheetId="1" r:id="rId1"/>
<sheet name="Resumo" sheetId="2" r:id="rId2"/>
<sheet name="Níveis" sheetId="3" r:id="rId3"/>
<sheet name="Arquivos" sheetId="4" r:id="rId4"/>
</sheets>
</workbook>
"""

_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2">
<font><sz val="11"/><name val="Calibri"/></font>
<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
</fonts>
<fills count="3">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF3A4FBF"/></patternFill></fill>
</fills>
<borders count="1"><border><left/><right/><top/><bottom/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="3">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
<xf numFmtId="3" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
</cellXfs>
</styleSheet>
"""


def _coluna(n):
    s = ""
    while n:
        n, resto = divmod(n - 1, 26)
        s = chr(65 + resto) + s
    return s


def _texto(valor):
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(valor))
    if len(texto) > 32000:
        texto = texto[:32000] + "…"
    return escape(texto)


def _celula(ref, valor, cabecalho=False):
    if cabecalho:
        return f'<c r="{ref}" s="1" t="inlineStr"><is><t>{_texto(valor)}</t></is></c>'
    if isinstance(valor, bool) or valor is None or valor == "":
        return ""
    if isinstance(valor, int):
        return f'<c r="{ref}" s="2"><v>{valor}</v></c>'
    texto = str(valor)
    espaco = ' xml:space="preserve"' if texto[:1].isspace() or texto[-1:].isspace() or "\n" in texto else ""
    return f'<c r="{ref}" t="inlineStr"><is><t{espaco}>{_texto(texto)}</t></is></c>'


def _folha(linhas, larguras):
    cols = "".join(
        f'<col min="{i}" max="{i}" width="{largura}" customWidth="1"/>'
        for i, largura in enumerate(larguras, 1)
    )
    ultima = f"{_coluna(max(len(linhas[0]), 1))}{len(linhas)}"
    filtro = f'<autoFilter ref="A1:{ultima}"/>' if len(linhas) > 1 else ""
    corpo = []
    for i, linha in enumerate(linhas, 1):
        cels = []
        for j, valor in enumerate(linha, 1):
            cels.append(_celula(f"{_coluna(j)}{i}", valor, cabecalho=i == 1))
        corpo.append(f'<row r="{i}">{"".join(cels)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        f"<cols>{cols}</cols>"
        f"<sheetData>{''.join(corpo)}</sheetData>"
        f"{filtro}</worksheet>"
    )


def _amostra(achado):
    amostras = achado.get("amostras") or []
    if not amostras:
        return ""
    return " / ".join((am.get("texto") or "").replace("\n", " / ") for am in amostras)


def xlsx_relatorio(relatorio):
    """Devolve os bytes de um .xlsx com Achados, Resumo, Níveis e Arquivos."""
    resumo = relatorio.get("resumo") or {}
    niveis = resumo.get("niveis") or {}
    achados = [[
        "Id", "Classe", "Nível", "Contagem", "Título", "Motivo", "Retorno", "Arquivos", "Amostra",
    ]]
    for a in relatorio.get("achados") or []:
        achados.append([
            a.get("id") or "",
            CLASSE.get(a.get("classe"), a.get("classe") or ""),
            NIVEL.get(a.get("nivel"), a.get("nivel") or ""),
            int(a.get("contagem") or 0),
            a.get("titulo") or "",
            a.get("motivo") or "",
            a.get("retorno") if isinstance(a.get("retorno"), int) else "",
            "; ".join(a.get("arquivos") or []),
            _amostra(a),
        ])
    quadro = [
        ["Métrica", "Valor"],
        ["Leitura", "Achados são problemas. Níveis são linhas do arquivo, saudáveis ou não."],
        ["Arquivos", int(resumo.get("arquivos") or 0)],
        ["Linhas", int(resumo.get("linhas") or 0)],
        ["Falsos negativos", int(resumo.get("falsos_negativos") or 0)],
        ["Erros", int(resumo.get("erros") or 0)],
        ["Avisos", int(resumo.get("avisos") or 0)],
        ["Falsos positivos", int(resumo.get("falsos_positivos") or 0)],
    ]
    niveis_linhas = [["Nível", "Linhas"]]
    for chave, rotulo in NIVEL.items():
        niveis_linhas.append([rotulo, int(niveis.get(chave) or 0)])
    arquivos = [["Nome", "Bytes", "Linhas", "Ignorado"]]
    for arq in relatorio.get("arquivos") or []:
        arquivos.append([
            arq.get("nome") or "",
            int(arq.get("bytes") or 0),
            int(arq.get("linhas") or 0),
            arq.get("ignorado") or "",
        ])
    pacote = {
        "[Content_Types].xml": _TIPOS,
        "_rels/.rels": _RELS,
        "xl/workbook.xml": _WORKBOOK,
        "xl/_rels/workbook.xml.rels": _WB_RELS,
        "xl/styles.xml": _STYLES,
        "xl/worksheets/sheet1.xml": _folha(achados, [10, 18, 14, 12, 56, 40, 12, 40, 64]),
        "xl/worksheets/sheet2.xml": _folha(quadro, [22, 72]),
        "xl/worksheets/sheet3.xml": _folha(niveis_linhas, [28, 14]),
        "xl/worksheets/sheet4.xml": _folha(arquivos, [42, 14, 12, 24]),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for nome, conteudo in pacote.items():
            z.writestr(nome, conteudo.encode("utf-8") if isinstance(conteudo, str) else conteudo)
    return buf.getvalue()
