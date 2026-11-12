---
name: logs
description: Analisa um ou mais logs (arquivo, pasta, zip ou tar), separa erro real, falso positivo e falso negativo, lê códigos de retorno e gera um painel HTML. Use quando a pessoa enviar logs, um zip ou tar de logs, ou pedir diagnóstico, erro escondido ou dashboard de logs.
argument-hint: "[arquivo, pasta, zip ou tar — um ou vários]"
---

# Análise de logs

Script determinístico, só biblioteca padrão: `python -I ../../scripts/analisar.py`.

## Passos
1. Um comando só aceita um arquivo de log, uma pasta, um `.gz`, ou um `.zip`/`.tar`/`.tar.gz`/`.tgz` com um log ou vários — e também vários desses juntos, zips e tars misturados com arquivos soltos. Um tar com milhares de `.log` entra inteiro. A saída, na mesma pasta, é `relatorio.json` (para o agente), `painel.html` (o painel) e `achados.xlsx` (a planilha).
2. Para a interface: `python -I ../../scripts/gui.py`. Abre `http://127.0.0.1:8765/`. A página tem uma área para soltar os arquivos. Vale um arquivo, vários, um zip ou tar, ou vários zips e tars no mesmo envio. O painel sai na mesma página: cartões de achado, barras do que mais aparece e o volume do arquivo em outra escala. A extração é o botão Baixar Excel. A página inicial lista as análises guardadas neste computador. `--porta` muda a porta. `--sem-navegador` não abre o browser.
3. Pelo terminal: `python -I ../../scripts/analisar.py <entradas> --saida .claude/local/logs/<nome>`. `<nome>` curto, sem espaço. `--estrito` devolve código 2 se houver erro ou falso negativo.
4. No terminal, leia `relatorio.json`. O painel é `painel.html` e a extração é `achados.xlsx`, na mesma pasta. Os números do feedback saem desse JSON. `resumo.niveis` conta linha do arquivo e não é o número do cartão. Na interface, leia o painel que a página mostrou.
5. O painel filtra a tabela por classe e pelo nível do achado. A busca é pelo título. Clicar numa barra isola aquele grupo. `resumo.niveis` conta cada bloco, saudável ou não, e aparece no cartão Volume do arquivo. Os mesmos bytes reabrem da guarda local sem reler. `DEVFLOW_LOGS_CACHE` troca a pasta; vazio desliga. No reenvio, a interface avisa que a leitura veio deste computador. A planilha tem as abas Achados, Resumo, Níveis e Arquivos.
6. Responda no formato abaixo. Reclassificar um achado exige arquivo, linha e uma frase de motivo.

## Classes
- **erro**: nível error/fatal, a palavra `Erro` na linha (mesmo sem `Exception`), exceção nesse nível, ou HTTP 5xx sem um nível mais baixo escondendo o fato.
- **falso_negativo**: a falha está no texto ou no retorno, mas o nível era info/warn/debug, ou o HTTP do cliente foi 2xx enquanto o corpo ou o upstream falhou. É o achado mais grave.
- **falso_positivo**: o sinal disparou e não é incidente. Caminho `/favicon.ico`, `/robots.txt` ou ícone da apple; `error_count=0`, `"error": null` ou `"errors": []`; cliente que fechou a conexão (`broken pipe`, `connection reset by peer`).
- **aviso**: HTTP 4xx que não é ruído (400, 401, 409, 422).
- **retornos**: cada código visto em `status` e em `upstream_status`, inclusive os 2xx saudáveis.

O script não trata 404 de `/health` como ruído: saúde quebrada aparece como aviso.

## Feedback
1. Uma frase: o que o conjunto mostra.
2. Falsos negativos, depois erros. Cada um com contagem, arquivos, amostra e a ação.
3. Retornos que mudam a leitura (5xx, e 2xx que mente).
4. Falsos positivos em uma linha.
5. Arquivos pulados (`ignorados`).
6. Caminho do `painel.html` e do `achados.xlsx`.
7. Contagem de `resumo.niveis` (erro, aviso, info, debug, sem nível).
