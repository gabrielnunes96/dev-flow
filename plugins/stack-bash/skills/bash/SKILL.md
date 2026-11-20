---
name: bash
description: Convenções para escrever, testar e revisar scripts de shell (Bash e sh POSIX) no fluxo — shebang e modo estrito, aspas em toda expansão, arrays, trap e limpeza com mktemp, validação de argumentos, códigos de saída, saída de erro em stderr, portabilidade Linux/macOS/Git Bash, segredos fora do script, ShellCheck, shfmt e testes com bats. Use ao criar ou revisar scripts .sh, entrypoints de container, passos de CI ou utilitários de linha de comando num projeto com stack bash.
---

# Bash e sh no fluxo

As convenções do **projeto** (pasta dos scripts, `Makefile`/`justfile`, estilo existente) vencem estas quando conflitarem. Modelo: `../../templates/script.sh` (relativo a esta skill).

Versões com suporte, LTS e mudanças recentes: `../../referencias/atual.md` (veja a data de revisão). Antes de usar API ou recurso, siga o procedimento *projeto primeiro* do fluxo (`referencias/conhecimento.md` do plugin `fluxo`): padrão do projeto → versão em uso → documentação daquela versão → novidade como sugestão.

## Escrever
- **Shell certo**: `#!/usr/bin/env bash` quando usa recurso de Bash (arrays, `[[ ]]`, `local`, `pipefail`); `#!/bin/sh` só com POSIX puro (imagem Alpine/distroless sem Bash, `ENTRYPOINT` mínimo). Não misturar: `sh script.sh` num script Bash quebra em silêncio.
- **Modo estrito** no topo: `set -Eeuo pipefail` (Bash) ou `set -eu` (sh). Conhecer os buracos do `-e`: não vale dentro de `if`, `&&`/`||`, `$(...)` em atribuição com `local x=$(...)` (separe `local x; x=$(...)`). Comando que pode falhar de propósito: `cmd || true` explícito ou `if ! cmd; then`. Outras armadilhas: função chamada em `if`/`&&`/`||` roda inteira sem `-e`; `((i++))` com `i=0` retorna 1 e encerra o script (use `i=$((i + 1))`); com `pipefail`, `cmd | head` ou `| grep -q` pode sair com 141 (SIGPIPE); `$(...)` só herda o `-e` com `shopt -s inherit_errexit` (Bash 4.4+).
- **Aspas em toda expansão**: `"$var"`, `"$@"`, `"${arr[@]}"`, `"$(cmd)"`. Sem aspas = divisão por espaço e glob. Exceção consciente comentada.
- **Listas em array**, nunca em string: `args=(--flag "$valor"); cmd "${args[@]}"`. Nada de `eval` para montar comando.
- **Entrada validada**: `usage()` + `getopts` (ou `case` em laço), obrigatórios checados (`: "${VAR:?defina VAR}"`), `--` antes de argumento que pode começar com `-` (`rm -- "$arq"`, `grep -- "$padrao"`).
- **Limpeza garantida**: `tmp=$(mktemp -d)` + `trap 'rm -rf -- "$tmp"' EXIT`; nunca nome fixo em `/tmp`. `trap` de `ERR` para mostrar linha e comando que falhou quando o script é longo.
- **`rm -rf` com variável**: `"${dir:?}"/` para nunca virar `rm -rf /`; conferir que o caminho está dentro da pasta esperada.
- **Saída**: mensagens e erros em stderr (`>&2`), dados em stdout (para poder encadear); código de saída significativo (0 ok, 1 erro, 2 uso errado, outros documentados). `printf` em vez de `echo` com variável (portabilidade de `-e`/`-n`).
- **Leitura de linhas**: `while IFS= read -r linha; do ...; done < arq`; arquivos com espaço no nome via `find ... -print0 | xargs -0` ou `-exec ... {} +`. Nunca `for f in $(ls)`.
- **Comparações**: `[[ ]]` no Bash (`==`, `=~`, sem aspas só à direita de `=~`); `(( ))` para aritmética. Em sh, `[ "$a" = "$b" ]` com aspas.
- **Portabilidade**: GNU × BSD/macOS (`sed -i`, `date -d`, `readlink -f`, `grep -P`); Git Bash no Windows (caminhos, CRLF — ver stack `git` para `.gitattributes` com `*.sh text eol=lf`). Se o script roda em mais de um, testar nos dois ou usar só o comum.
- **Segredos**: nunca no script nem em argumento de linha de comando (aparece no `ps` e no histórico); vir de variável de ambiente, arquivo com permissão restrita ou cofre do CI. `set -x` só com segredo mascarado.
- **Download e execução**: nada de `curl ... | sh` sem versão fixa e verificação de checksum/assinatura. `curl -fsSL` (falha em HTTP de erro).
- **Idempotente** quando possível (rodar duas vezes não estraga): `mkdir -p`, checar antes de criar, `ln -sfn`.
- Script cresceu (estrutura de dados, JSON, mais de ~150 linhas de lógica)? Propor reescrever na linguagem do projeto — não é decisão da tarefa.

## Testar
- `shellcheck` em todo script alterado, sem aviso novo (`# shellcheck disable=SCxxxx` só com motivo no comentário). `shfmt -d` se o projeto usa.
- Testes com **bats** (`bats-core`) quando o script tem lógica: argumentos inválidos, caminho feliz, falha de dependência, nome de arquivo com espaço. Sem bats no projeto: rodar os casos à mão e registrar a tabela no card.
- `bash -n script.sh` (sintaxe) no mínimo; rodar com `bash -x` para depurar, sem segredo na saída.
- Rodar no shell e no sistema de destino (imagem do container, runner do CI), não só na máquina de quem escreveu.

## Checklist de revisão
1. Shebang condiz com os recursos usados; modo estrito ligado (`set -Eeuo pipefail` ou `set -eu`).
2. Toda expansão entre aspas; listas em array; nenhum `eval` ou `for f in $(ls)`.
3. Argumentos validados com mensagem de uso; `--` antes de valor que pode começar com `-`.
4. Temporários com `mktemp` e `trap` de limpeza; `rm -rf` protegido com `${var:?}`.
5. Erros em stderr e código de saída significativo; falha esperada tratada de forma explícita.
6. Nenhum segredo no script, em argumento ou em `set -x`; nada de `curl | sh` sem verificação.
7. ShellCheck sem aviso novo; testes (bats ou tabela manual) cobrindo entrada inválida e caminho feliz.
8. Funciona no ambiente de destino (sh × bash, GNU × BSD, fim de linha LF).
