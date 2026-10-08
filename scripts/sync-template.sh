#!/usr/bin/env bash
# Copia os arquivos canônicos (template/) para os repositórios dos componentes.
#
#   scripts/sync-template.sh                      todos os TEC.* vizinhos deste repositório
#   scripts/sync-template.sh ../TEC.Vault ...     só os informados
#
# Os arquivos de template/ nunca são editados nos componentes: o job "Convenções" do CI compara as cópias.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$ROOT/template"

if [ "$#" -eq 0 ]; then
  set -- "$ROOT"/../TEC.*
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
