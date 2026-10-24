#!/usr/bin/env bash
# --------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Roberto Oliveira / Tudo em Código.
# Autor: Roberto Oliveira | Criação: 2026-10-24
# Licenciado sob a Licença Apache, Versão 2.0. Consulte LICENSE e NOTICE na raiz.
# --------------------------------------------------------------------------------------------------------------------
# Copia os arquivos canônicos (template/) para os repositórios dos componentes.
#
#   scripts/sync-template.sh                      todos os TEC.* vizinhos deste repositório
#   scripts/sync-template.sh ../TEC.Vault ...     só os informados
#
# Os arquivos de template/ nunca são editados nos componentes: o job "Convenções" do CI compara as cópias.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$ROOT/template"

# Copia a cópia de trabalho: alteração não commitada (ou ainda sem tag) em template/ faz o job Convenções dos
# componentes falhar, porque ele compara com o template/ da tag usada (@v1). Ordem: commit aqui -> tag -> componentes.
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 &&
  [ -n "$(git -C "$ROOT" status --porcelain -- template)" ]; then
  echo "AVISO: template/ tem alterações não commitadas; o job Convenções dos componentes compara com a tag publicada." >&2
fi

if [ "$#" -eq 0 ]; then
  shopt -s nullglob
  repos=("$ROOT"/../TEC.* "$ROOT"/../lib-tec-*)
  shopt -u nullglob
  set -- "${repos[@]}"
fi

for repo in "$@"; do
  if [ ! -d "$repo" ]; then
    echo "Ignorado (não é pasta): $repo" >&2
    continue
  fi
  (cd "$TEMPLATE" && find . -type f -print0) | while IFS= read -r -d '' file; do
    mkdir -p "$repo/$(dirname "$file")"
    cp "$TEMPLATE/$file" "$repo/$file"
  done
  echo "Sincronizado: $(cd "$repo" && pwd)"
done
