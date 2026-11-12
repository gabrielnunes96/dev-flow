# Gera docs/manual-dev-flow.pdf (precisa de reportlab; usa Segoe UI/Consolas no Windows e Liberation Sans/Mono fora dele).
# Uso: python docs/gerar_manual.py docs/manual-dev-flow.pdf
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, Preformatted, KeepTogether)

import os

# Segoe UI/Consolas no Windows; fora dele, Liberation Sans/Mono (pacote fonts-liberation).
F = "C:/Windows/Fonts/"
L = "/usr/share/fonts/truetype/liberation/"
if os.path.exists(F + "segoeui.ttf"):
    FONTES = {"Segoe": F + "segoeui.ttf", "Segoe-B": F + "segoeuib.ttf", "Segoe-I": F + "segoeuii.ttf",
              "Segoe-BI": F + "segoeuiz.ttf", "Consolas": F + "consola.ttf"}
else:
    FONTES = {"Segoe": L + "LiberationSans-Regular.ttf", "Segoe-B": L + "LiberationSans-Bold.ttf",
              "Segoe-I": L + "LiberationSans-Italic.ttf", "Segoe-BI": L + "LiberationSans-BoldItalic.ttf",
              "Consolas": L + "LiberationMono-Regular.ttf"}
for nome, arquivo in FONTES.items():
    pdfmetrics.registerFont(TTFont(nome, arquivo))
pdfmetrics.registerFontFamily("Segoe", normal="Segoe", bold="Segoe-B", italic="Segoe-I", boldItalic="Segoe-BI")

AZUL = colors.HexColor("#1F3A5F")
AZUL_CLARO = colors.HexColor("#E8EEF6")
CINZA = colors.HexColor("#5A6270")
LINHA = colors.HexColor("#C9D3E0")
AMARELO = colors.HexColor("#FFF6D6")

base = ParagraphStyle("base", fontName="Segoe", fontSize=10, leading=14.5, spaceAfter=5)
h1 = ParagraphStyle("h1", parent=base, fontName="Segoe-B", fontSize=17, leading=22, textColor=AZUL, spaceBefore=4, spaceAfter=8)
h2 = ParagraphStyle("h2", parent=base, fontName="Segoe-B", fontSize=12.5, leading=17, textColor=AZUL, spaceBefore=10, spaceAfter=4)
cel = ParagraphStyle("cel", parent=base, fontSize=9, leading=12.5, spaceAfter=0)
celb = ParagraphStyle("celb", parent=cel, fontName="Segoe-B", textColor=colors.white)
bul = ParagraphStyle("bul", parent=base, leftIndent=14, bulletIndent=4, spaceAfter=3)
nota = ParagraphStyle("nota", parent=base, fontSize=9.5, leading=13.5)
code = ParagraphStyle("code", fontName="Consolas", fontSize=8.6, leading=11.5, textColor=colors.HexColor("#1B1F24"))


def c(t):
    return f'<font name="Consolas" size="9">{t}</font>'


def P(t, s=base):
    return Paragraph(t, s)


def bullets(itens):
    return [Paragraph(i, bul, bulletText="•") for i in itens]


def tabela(cab, linhas, larguras):
    dados = [[Paragraph(x, celb) for x in cab]] + [[Paragraph(x, cel) for x in l] for l in linhas]
    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, AZUL_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.4, LINHA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def caixa(conteudo, fundo=AZUL_CLARO):
    t = Table([[conteudo]], colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fundo), ("BOX", (0, 0), (-1, -1), 0.5, LINHA),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def bloco_codigo(texto):
    return caixa(Preformatted(texto, code), colors.HexColor("#F3F5F8"))


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Segoe", 8)
    canvas.setFillColor(CINZA)
    canvas.drawString(20 * mm, 12 * mm, "dev-flow · Manual do time")
    canvas.drawRightString(190 * mm, 12 * mm, f"Página {doc.page}")
    canvas.setStrokeColor(LINHA)
    canvas.line(20 * mm, 16 * mm, 190 * mm, 16 * mm)
    canvas.restoreState()


def capa(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(AZUL)
    canvas.rect(0, A4[1] - 95 * mm, A4[0], 95 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Segoe-B", 34)
    canvas.drawString(20 * mm, A4[1] - 50 * mm, "dev-flow")
    canvas.setFont("Segoe", 15)
    canvas.drawString(20 * mm, A4[1] - 62 * mm, "Manual do time")
    canvas.setFont("Segoe", 11)
    canvas.drawString(20 * mm, A4[1] - 75 * mm, "Fluxo de desenvolvimento com Claude Code: da demanda ao PR e à pipeline")
    canvas.restoreState()


s = []
# ---------------- capa ----------------
s.append(Spacer(1, 92 * mm))
s.append(P("O que você vai encontrar aqui", h2))
s += bullets([
    "O que é o dev-flow e que problema ele resolve",
    "O fluxo de ponta a ponta: demanda, funcional, técnica, plano, tarefas, PR e pipeline",
    "Os plugins, os agentes e o que cada um integra (git, Azure Boards, Azure Pipelines, ambiente local)",
    "Como instalar, configurar um projeto e usar no dia a dia",
    "As proteções automáticas e o que continua sendo decisão humana",
])
s.append(Spacer(1, 10))
s.append(caixa(P("<b>Em uma frase:</b> você explica a demanda em texto; o Claude Code escreve a especificação funcional e a técnica, "
                 "monta o plano, implementa tarefa por tarefa (com testes, revisão, validação e commit) e prepara o PR, "
                 "parando para a sua aprovação nos pontos que importam.", nota)))
s.append(Spacer(1, 10))
s.append(P(f"Versão dos plugins: 0.1.0 · Outubro/2026", ParagraphStyle("v", parent=nota, textColor=CINZA)))
s.append(PageBreak())

# ---------------- 1. o que é ----------------
s.append(P("1. O que é", h1))
s.append(P("O <b>dev-flow</b> é um <i>marketplace de plugins</i> do Claude Code. Cada plugin traz skills (comandos como "
           f"{c('/fluxo:demanda')}), agentes especializados e hooks (verificações automáticas que rodam antes de cada ação do Claude)."))
s.append(P("Ele nasceu da forma como o PBI 1001 (Acme.API.Ponte) foi desenvolvido: specs antes de código, tarefas pequenas, "
           "testes e validação real em cada tarefa, card atualizado com evidências e um commit por tarefa. O processo foi extraído "
           "para servir a qualquer projeto: back-end, front-end, scripts SQL ou vários repositórios na mesma demanda."))
s.append(P("Por que plugin (e não MCP ou instruções soltas)", h2))
s += bullets([
    "<b>Processo é texto + scripts</b>: skills dizem ao modelo <i>como</i> trabalhar; scripts determinísticos fazem o que não pode depender de memória (fila de tarefas, chamadas de validação, bloqueios).",
    "<b>Instala uma vez, vale em todo projeto</b>: o que muda entre projetos fica num arquivo de perfil ("
    f"{c('.claude/projeto.json')}), não no plugin.",
    "<b>Acoplável</b>: instale só as stacks que você usa (.NET, SQL, front) e o Azure Boards só se o projeto usar.",
    "<b>Proteções reais</b>: o hook <i>guard</i> bloqueia de fato (push, segredo em commit, arquivo gerado, diretório proibido), em vez de depender do modelo lembrar.",
])
s.append(P("Responsabilidades", h2))
s.append(tabela(["O Claude faz", "Você decide / faz"], [
    ["Escreve funcional, técnica e plano a partir do código real", "Aprova (ou corrige) funcional, técnica e plano"],
    ["Implementa, testa, revisa, valida e commita cada tarefa", "Responde dúvidas de regra de negócio"],
    ["Cria/atualiza cards no Boards (depois do seu \"sim\")", "Faz push, abre/mergeia o PR"],
    ["Gera o YAML de pipeline e diagnostica falhas", "Aprova deploy em produção (no environment)"],
], [85 * mm, 85 * mm]))
s.append(PageBreak())

# ---------------- 2. ponta a ponta ----------------
s.append(P("2. O fluxo de ponta a ponta", h1))
s.append(bloco_codigo(
    "demanda (você explica em texto)\n"
    "  → /fluxo:demanda  → 01-funcional.md                (*) você aprova\n"
    "  → /fluxo:tecnica  → 02-tecnica.md (código real)     (*) você aprova\n"
    "  → /fluxo:plano    → tarefas.json + 03-plano.md      (*) você aprova  (+ cards no Boards, opcional)\n"
    "  → /fluxo:task todas → por tarefa: implementa → testa → revisor → validador → commit → feito\n"
    "  → /fluxo:pr       → pr.md (+ PR aberto depois do seu push)\n"
    "  → azure-pipelines → CI verde; deploy em produção com aprovação no environment\n\n"
    "/fluxo:entregar faz tudo isso em sequência, parando só nos (*)."))
s.append(Spacer(1, 6))
s.append(tabela(["Etapa", "Entrada", "Saída", "Portão"], [
    [c("/fluxo:demanda"), "Seu texto (pedido, e-mail, print, conversa)", "01-funcional.md: regras de negócio, requisitos, critérios de aceite (CA-n), fora de escopo, dúvidas", "Você aprova"],
    [c("/fluxo:tecnica"), "Funcional aprovada + código dos repositórios afetados (agente analista)", "02-tecnica.md: componentes, contratos, dados, integrações, segurança, testes por CA, riscos, implantação/CI", "Você aprova"],
    [c("/fluxo:plano"), "Técnica aprovada", "tarefas.json (fila) + 03-plano.md: tarefas pequenas, dependências, critérios e validação de cada uma", "Você aprova"],
    [c("/fluxo:task"), "Próxima tarefa pronta da fila", "Código + testes + commit; tarefa marcada como feita; card publicado (se Boards)", "Para se houver dúvida"],
    [c("/fluxo:pr"), "Fila concluída", "pr.md: o que muda, impacto, validação, pendências, implantação", "Push/merge são seus"],
    ["azure-pipelines", "Stack do projeto", "YAML de CI/CD por stack; deploy por ambiente", "Produção com aprovação"],
], [33 * mm, 38 * mm, 71 * mm, 28 * mm]))
s.append(P("Documentos de uma demanda", h2))
s.append(bloco_codigo(
    "{docs}/{slug}/\n"
    "  00-demanda.md     texto original do pedido\n"
    "  01-funcional.md   RN, RF, critérios de aceite (CA-n), fora de escopo, dúvidas\n"
    "  02-tecnica.md     componentes, contratos, dados, testes por CA, riscos, implantação\n"
    "  03-plano.md       ordem, paralelismo, definição de pronto\n"
    "  tarefas.json      fila (fonte da verdade): id, critérios, dependências, estado, wi, commit\n"
    "  pr.md             descrição do PR"))
s.append(P(f"O {c('tarefas.json')} é a fonte da verdade: estados {c('a_fazer')}, {c('andamento')}, {c('feito')}, {c('bloqueada')}. "
           "Uma tarefa está pronta quando todas as dependências estão feitas. Tarefas marcadas como protegidas nunca são executadas pelo Claude.", nota))
s.append(PageBreak())

# ---------------- 3. ciclo da tarefa ----------------
s.append(P("3. O ciclo de uma tarefa", h1))
s.append(P(f"É o coração do fluxo ({c('/fluxo:task')}). Cada tarefa passa pelos mesmos passos, sempre:"))
s.append(tabela(["#", "Passo", "O que acontece"], [
    ["0", "Pré-condições", "Valida o perfil, confere git limpo, gera o token de validação (se houver) e carrega as skills das stacks do projeto."],
    ["1", "Escolher", "Pega a próxima tarefa pronta da fila (ou a que você indicou), marca em andamento e move o card."],
    ["2", "Implementar", "Segue o padrão do código existente e as convenções da stack e do projeto."],
    ["3", "Testes", "Roda o comando de testes do perfil; teste novo para cada critério de aceite que couber."],
    ["4", "Revisão", "Agente <b>revisor</b> confere critérios de aceite, convenções e checklist da stack; achados graves são corrigidos antes de seguir."],
    ["5", "Validação", "Agente <b>validador</b> roda no ambiente real: sobe a API e chama as rotas, aplica e reverte SQL, roda um comando ou confere a tela."],
    ["6", "Commit", "Um commit por tarefa, no formato do perfil. O guard bloqueia commit com segredo."],
    ["7", "Registro", "Atualiza tarefas.json (commit, nota) e publica o card com Implementação, Testes e Validação."],
    ["8", "Fechamento", "Marca feito e resume o que foi feito, o que ficou pendente e o que depende de você."],
], [8 * mm, 27 * mm, 135 * mm]))
s.append(Spacer(1, 6))
s.append(caixa(P("<b>Quando o Claude para e pergunta:</b> regra de negócio ambígua, algo fora do escopo da demanda, "
                 "falha de validação sem causa clara, alteração pendente que não é dele, ou qualquer situação listada em "
                 f"{c('pare_e_pergunte')} no perfil do projeto.", nota), AMARELO))
s.append(P("Agentes", h2))
s.append(tabela(["Agente", "Quando entra", "O que devolve"], [
    ["analista", "Especificação técnica (um por repositório, em paralelo)", "Onde e como os requisitos entram no código: arquivos-chave com linha, padrões, contratos, riscos. Somente leitura."],
    ["revisor", "Passo 4 do ciclo", "Achados objetivos com arquivo:linha, classificados por gravidade. Somente leitura."],
    ["validador", "Passo 5 do ciclo", "Tabela Chamada | Status | Resultado, pronta para o card."],
], [25 * mm, 55 * mm, 90 * mm]))
s.append(PageBreak())

# ---------------- 4. plugins e integrações ----------------
s.append(P("4. Plugins e o que cada um integra", h1))
s.append(tabela(["Plugin", "O que traz", "Integra com"], [
    ["<b>fluxo</b> (núcleo, obrigatório)", "Skills iniciar, demanda, tecnica, plano, task, entregar, pr, status, daily, aprender; agentes analista, revisor, validador; hooks guard e contexto; scripts da fila, validação HTTP, subir/derrubar serviço e token; modelos de documento.", "Claude Code, git, ambiente local (API, banco de dev, comandos)"],
    ["<b>azure-boards</b>", "Cria o PBI e as tasks a partir do plano, move estados, publica a descrição do card, importa um PBI existente.", "Azure Boards (via MCP do Azure DevOps ou az boards)"],
    ["<b>azure-pipelines</b>", "Modelos YAML (dotnet, front, sql, deploy por ambiente); criar, ajustar e diagnosticar pipelines.", "Azure Pipelines / environments"],
    ["<b>stack-dotnet</b>", "Convenções, armadilhas e checklist .NET; modelo de API em memória para testes de contrato.", "dotnet build/test"],
    ["<b>stack-sql</b>", "Convenções SQL Server (idempotência, rollback pareado, lote); modelos de script e rollback.", "Banco de desenvolvimento"],
    ["<b>stack-front</b>", "Convenções de front, verificação visual no navegador (desktop e mobile), checklist.", "Navegador"],
    ["<b>design</b>", "Designer de UX/UI: direção visual, tema claro/escuro com tokens, telas, animações limpas, acessibilidade e revisão visual.", "Navegador, stack-front"],
    ["<b>logs</b>", "Interface no navegador e script: um arquivo, vários, ou vários zips e tars. Separa erro, falso positivo e falso negativo e mostra o painel.", "Navegador em 127.0.0.1"],
    ["<b>video</b>", "Vídeo-resumo a partir de um roteiro JSON. Este manual não traz o passo a passo; ele está na skill video do plugin.", "Python e as dependências do plugin"],
], [33 * mm, 87 * mm, 50 * mm]))
s.append(P("Hooks (rodam sozinhos)", h2))
s += bullets([
    "<b>contexto</b> (início da sessão): mostra o projeto, a demanda ativa e a próxima tarefa pronta. Sem perfil, sugere "
    f"{c('/fluxo:iniciar')}.",
    "<b>guard</b> (antes de cada ação): aplica as proteções do perfil e bloqueia de verdade. Detalhes na seção 7.",
])
s.append(P("O perfil do projeto (.claude/projeto.json)", h2))
s.append(P("É o contrato entre o processo genérico e o seu projeto. As skills não têm nada fixo: comando, porta, id de card, caminho, tudo vem daqui."))
s.append(tabela(["Seção", "Para quê"], [
    [c("stacks, convencoes"), "Quais skills de stack e quais arquivos de convenção valem"],
    [c("docs"), "Onde ficam as especificações e o tarefas.json"],
    [c("rastreador"), "Local ou Azure Boards (org, item raiz, protegidos, estados)"],
    [c("comandos"), "Build, teste, lint, verificação de pacotes vulneráveis"],
    [c("servico, validacao"), "Como subir a aplicação, token, URL, dados de teste, casos obrigatórios, máscaras de segredo"],
    [c("git"), "Branch base, formato do commit, coautor, push humano"],
    [c("protecao"), "Textos/diretórios proibidos, arquivos gerados, segredos (o guard aplica)"],
    [c("design"), "Arquivo de tokens, design system, plataformas e referências de marca (plugin design)"],
    [c("pare_e_pergunte"), "Situações do projeto em que o ciclo para"],
], [45 * mm, 125 * mm]))
s.append(PageBreak())

# ---------------- 5. instalação e primeiro uso ----------------
s.append(P("5. Instalação e primeiro uso", h1))
s.append(P("Pré-requisitos", h2))
s += bullets([
    "Claude Code (terminal, app desktop ou extensão de IDE) e Python 3 no PATH (os scripts usam só a biblioteca padrão).",
    "Acesso ao repositório do dev-flow.",
    "Para Boards: MCP do Azure DevOps configurado na máquina (seção 6).",
])
s.append(P("Instalar (uma vez por máquina)", h2))
s.append(bloco_codigo(
    "claude plugin marketplace add <caminho ou URL do repositório dev-flow>\n"
    "claude plugin install fluxo@dev-flow\n"
    "claude plugin install stack-dotnet@dev-flow     # conforme as stacks que você usa\n"
    "claude plugin install stack-sql@dev-flow\n"
    "claude plugin install stack-front@dev-flow\n"
    "claude plugin install design@dev-flow           # tema, telas e animações\n"
    "claude plugin install logs@dev-flow             # análise de logs, com interface\n"
    "claude plugin install video@dev-flow            # vídeo-resumo; o uso está na skill\n"
    "claude plugin install azure-boards@dev-flow     # se for usar o Boards\n"
    "claude plugin install azure-pipelines@dev-flow  # se for gerar pipelines"))
s.append(P(f"Para conferir: {c('claude plugin list')}. Os plugins valem a partir da próxima sessão do Claude Code.", nota))
s.append(P("Preparar um projeto (uma vez por projeto)", h2))
s += bullets([
    "Abra o Claude Code na pasta do projeto (pode estar vazia).",
    f"Rode {c('/fluxo:iniciar')}: detecta a stack e os comandos, cria {c('.claude/projeto.json')}, um {c('CLAUDE.md')} enxuto se não houver, a pasta de especificações, e faz {c('git init')} se precisar.",
    "Revise o perfil: comandos de build/teste, como validar e o que é proibido mexer.",
])
s.append(P("Usar numa demanda", h2))
s.append(P(f"<b>Tudo de uma vez:</b> {c('/fluxo:entregar')} e explique a demanda em texto livre. <b>Passo a passo:</b>"))
s.append(tabela(["Comando", "Gera", "Você"], [
    [c("/fluxo:demanda"), "01-funcional.md", "Responde as dúvidas e aprova"],
    [c("/fluxo:tecnica"), "02-tecnica.md", "Aprova"],
    [c("/fluxo:plano"), "tarefas.json + 03-plano.md", "Aprova"],
    [c("/fluxo:task todas"), "Código, testes e um commit por tarefa", "Acompanha"],
    [c("/fluxo:pr"), "pr.md", "Push e PR"],
], [40 * mm, 75 * mm, 55 * mm]))
s.append(P("No dia a dia", h2))
s.append(tabela(["Comando", "Para quê"], [
    [c("/fluxo:status"), "Onde paramos, o que falta, bloqueios e divergências com o Boards"],
    [c("/fluxo:task") + " / " + c("/fluxo:task T3"), "Só a próxima tarefa / uma tarefa específica"],
    [c("/fluxo:daily"), "Relatório da daily (ontem, situação, hoje, impedimentos)"],
    [c("/fluxo:aprender"), "Transforma uma correção (\"isso não é assim\") em regra durável no lugar certo"],
], [55 * mm, 115 * mm]))
s.append(P("Interface de logs", h2))
s.append(P(
    f"No repositório do dev-flow, ou na pasta do plugin instalado: {c('python -I plugins/logs/scripts/gui.py')}. "
    "Abre uma página em 127.0.0.1:8765. Envie um arquivo, vários, um zip ou tar, ou vários zips e tars juntos. "
    "O painel (falso negativo, erro, aviso, falso positivo e os retornos HTTP) aparece na mesma página."
))
s.append(P(
    f"Pelo terminal, o mesmo motor: {c('python -I plugins/logs/scripts/analisar.py arquivos --saida .claude/local/logs/nome')}. "
    f"Grava {c('relatorio.json')} e {c('painel.html')}."
))
s.append(PageBreak())

# ---------------- 6. Boards ----------------
s.append(P("6. Azure Boards (opcional)", h1))
s.append(P(f"Sem configuração, tudo fica no {c('tarefas.json')} e nada vai para o Azure. Para publicar cards como no PBI 1001:"))
s.append(P("1. Conectar o Azure DevOps (uma vez por máquina)", h2))
s.append(bloco_codigo("claude mcp add azure-devops -- cmd /c npx -y @azure-devops/mcp <org> -d core work work-items"))
s.append(P("2. Configurar o projeto (uma vez)", h2))
s.append(P(f"Preencha {c('rastreador')} no perfil, ou peça \"configura o Boards neste projeto, iteração X\":"))
s.append(bloco_codigo(
    '"rastreador": {\n'
    '  "tipo": "azure-boards",\n'
    '  "org": "https://dev.azure.com/<organização>",\n'
    '  "projeto": "MeuProjeto",\n'
    '  "area": "MeuProjeto\\\\Equipe",\n'
    '  "iteracao": "MeuProjeto\\\\<sprint>",\n'
    '  "responsavel": "<seu e-mail>",\n'
    '  "item_raiz": null,\n'
    '  "protegidos": [],\n'
    '  "estados": { "a_fazer": "To Do", "andamento": "In Progress", "feito": "Done" }\n'
    '}'))
s += bullets([
    f"{c('item_raiz')} vazio: o PBI é criado a partir da funcional.",
    "PBI que já existe: coloque o número. Se ele já tem tasks, peça \"importa o PBI 2000\" para trazê-las ao tarefas.json.",
])
s.append(P("3. O que acontece no fluxo", h2))
s.append(tabela(["Momento", "No Boards"], [
    ["Plano aprovado", "Mostra a lista de PBI e tasks e só cria depois do seu \"sim\""],
    ["Início de cada tarefa", "Move a task para In Progress"],
    ["Fim de cada tarefa", "Publica a descrição do card (Implementação, Testes, Validação) e marca Done"],
    [c("/fluxo:status"), "Compara o Boards com o tarefas.json e aponta divergências"],
], [45 * mm, 125 * mm]))
s.append(P("Pedidos avulsos: \"cria os cards no Boards\", \"publica o card da T3\", \"move a task 2010 para In Progress\".", nota))
s.append(caixa(P("<b>Limites:</b> só o PBI do perfil e as tasks filhas dele; itens em <i>protegidos</i> nunca são movidos nem editados; "
                 "toda atualização confere a revisão do card antes de gravar, para não sobrescrever edição de outra pessoa.", nota), AMARELO))
s.append(PageBreak())

# ---------------- 7. proteções e evolução ----------------
s.append(P("7. Proteções automáticas", h1))
s.append(P("O hook <b>guard</b> roda antes de cada ação do Claude e bloqueia de fato (a ação não acontece), conforme o perfil:"))
s.append(tabela(["Regra", "Bloqueia"], [
    ["Push humano", f"Qualquer {c('git push')} (o padrão quando há perfil)"],
    ["Segredo em commit", "Commit cujo diff tenha JWT, chave privada, chave AWS, token do GitHub ou padrões extras do perfil (sempre ativo)"],
    ["Diretórios proibidos", "Ler, editar ou buscar dentro deles (ex.: cópias antigas que não podem servir de referência)"],
    ["Arquivos gerados", "Editar à mão código gerado (SDKs, proxies), com exceções declaradas"],
    ["Segredos", "Ler arquivos de token/credencial ou citá-los em comandos, exceto pelos scripts autorizados"],
    ["Textos proibidos", "Ações cujo conteúdo case com expressões proibidas no perfil"],
], [40 * mm, 130 * mm]))
s.append(P("Além disso: o validador mascara segredos nas saídas, o token nunca é impresso e certificados de ambiente de homologação são conferidos por impressão digital (sem desligar TLS).", nota))
s.append(P("8. Como o processo evolui", h1))
s += bullets([
    f"<b>Correção de um projeto só</b> (comando, regra, dado de teste): vai no {c('projeto.json')} ou no {c('CLAUDE.md')} daquele projeto.",
    "<b>Correção que vale para todos</b> (passo do ciclo, modelo de documento, checklist de stack): vai no repositório dev-flow, com teste em tests/.",
    f"Use {c('/fluxo:aprender')} ao fim de uma demanda ou quando corrigir o Claude: ele decide o lugar certo e registra.",
    "Mudanças valem a partir da próxima sessão. Nova stack = um plugin pequeno (ver docs/novo-plugin-de-stack.md).",
])
s.append(P("9. Perguntas frequentes", h1))
faq = [
    ("Preciso usar o fluxo inteiro?", f"Não. Cada skill funciona sozinha: dá para usar só {c('/fluxo:demanda')} para escrever uma funcional, ou só {c('/fluxo:task')} numa fila que já existe."),
    ("Funciona sem Azure?", f"Sim. Com {c('rastreador.tipo = local')} tudo fica no tarefas.json; o Boards entra quando você quiser."),
    ("E projetos com vários repositórios?", "A técnica roda um agente analista por repositório e o plano indica em qual repositório cada tarefa entra."),
    ("O Claude pode fazer push ou deploy?", "Não. Push, merge e produção são sempre humanos; o guard bloqueia o push."),
    ("A sessão foi compactada / caiu. Perco o andamento?", f"Não. O estado está em arquivo (tarefas.json, documentos, commits). {c('/fluxo:status')} retoma de onde parou."),
]
for p_, r in faq:
    s.append(KeepTogether([P(f"<b>{p_}</b>", ParagraphStyle("q", parent=base, spaceAfter=1)), P(r, nota)]))

saida = sys.argv[1]
doc = SimpleDocTemplate(saida, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=22 * mm,
                        title="dev-flow — Manual do time", author="dev-flow", subject="Fluxo de desenvolvimento com Claude Code")
doc.build(s, onFirstPage=capa, onLaterPages=rodape)
print("ok", saida)
