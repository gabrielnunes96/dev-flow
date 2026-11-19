#!/usr/bin/env bash
# <o que este script faz, em uma linha>
# Uso: script.sh [-n] <entrada>
set -Eeuo pipefail

usage() {
  printf 'Uso: %s [-n] <entrada>\n  -n  simula, sem alterar nada\n' "${0##*/}" >&2
  exit 2
}

erro() { printf 'erro: %s\n' "$*" >&2; exit 1; }

trap 'printf "falhou na linha %s: %s\n" "$LINENO" "$BASH_COMMAND" >&2' ERR

simular=0
while getopts ':nh' opt; do
  case "$opt" in
    n) simular=1 ;;
    h | *) usage ;;
  esac
done
shift $((OPTIND - 1))
[[ $# -eq 1 ]] || usage
entrada=$1
[[ -e "$entrada" ]] || erro "não encontrado: $entrada"

tmp=$(mktemp -d)
trap 'rm -rf -- "${tmp:?}"' EXIT

# ... trabalho aqui, sempre com "$variavel" entre aspas ...
if ((simular)); then
  printf 'simulação: processaria %s\n' "$entrada" >&2
fi
