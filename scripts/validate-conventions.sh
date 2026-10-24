#!/usr/bin/env bash
# --------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Roberto Oliveira / Tudo em Código.
# Autor: Roberto Oliveira | Criação: 2026-10-24
# Licenciado sob a Licença Apache, Versão 2.0. Consulte LICENSE e NOTICE na raiz.
# --------------------------------------------------------------------------------------------------------------------
# Valida localmente as convenções que o job "Convenções" do CI verifica.
# Uso: scripts/validate-conventions.sh [caminho-do-repositorio]
#   Se omitido, valida o diretório atual.
# Retorna 0 se tudo ok, 1 se houver divergências.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$ROOT/template"
REPO="${1:-$(pwd)}"

echo "Validando convenções em: $REPO"
echo "Template de referência: $TEMPLATE"
echo

rc=0

# 1. Arquivos canônicos
echo "=== 1. Arquivos canônicos ==="
while IFS= read -r -d '' file; do
  rel="${file#./}"
  target="$REPO/$rel"
  if [ ! -f "$target" ]; then
    echo "❌ FALTANDO: $rel (rode scripts/sync-template.sh do tec-workflows)"
    rc=1
  elif ! cmp -s "$TEMPLATE/$rel" "$target"; then
    echo "❌ DIVERGÊNCIA: $rel difere do template (edite em template/ e rode scripts/sync-template.sh)"
    rc=1
  else
    echo "✅ OK: $rel"
  fi
done < <(cd "$TEMPLATE" && find . -type f -print0)

# 2. NOTICE
echo
echo "=== 2. Arquivo NOTICE ==="
if [ ! -f "$REPO/NOTICE" ]; then
  echo "❌ FALTANDO: NOTICE na raiz do repositório (exigido pela convenção TEC)"
  rc=1
else
  echo "✅ OK: NOTICE presente"
fi

# 3. Convenções dos projetos (.csproj)
echo
echo "=== 3. Convenções dos projetos (.csproj) ==="
while IFS= read -r -d '' proj; do
  proj_rel="${proj#./}"
  proj_errors=0

  # PackageReference com Version ou VersionOverride
  if grep -Eq '<PackageReference[^>]+Version=' "$proj" || grep -Eq 'VersionOverride=' "$proj"; then
    echo "❌ $proj_rel: PackageReference com Version ou VersionOverride — declare a versão no Directory.Packages.props"
    proj_errors=1
  fi

  # Componente TEC.* via PackageReference
  if grep -Eq '<PackageReference[^>]+Include="TEC\.' "$proj"; then
    echo "❌ $proj_rel: Componente TEC.* via PackageReference — use <TecReference Include=\"TEC.X\" />"
    proj_errors=1
  fi

  # Versão no csproj
  if grep -Eq '<(Version|PackageVersion|VersionPrefix|VersionSuffix)>' "$proj"; then
    echo "❌ $proj_rel: Versão no csproj (<Version>, <PackageVersion>, <VersionPrefix>, <VersionSuffix>) — a versão é única por repositório (Directory.Build.props)"
    proj_errors=1
  fi

  # Directory.Packages.props: versões declaradas e não duplicadas
  if [ -f "$REPO/Directory.Packages.props" ]; then
    # Verifica se há PackageVersion duplicado
    dupes=$(grep -E '<PackageVersion[^>]+Include=' "$REPO/Directory.Packages.props" | sed -E 's/.*Include="([^"]+)".*/\1/' | sort | uniq -d)
    if [ -n "$dupes" ]; then
      echo "❌ $proj_rel: Directory.Packages.props tem PackageVersion duplicado(s): $dupes"
      proj_errors=1
    fi
    # Verifica se PackageVersion tem Version
    if grep -Eq '<PackageVersion[^>]+Version=' "$REPO/Directory.Packages.props"; then
      echo "❌ $proj_rel: Directory.Packages.props tem PackageVersion com atributo Version — use o conteúdo do elemento"
      proj_errors=1
    fi
  fi

  if [ "$proj_errors" -eq 0 ]; then
    echo "✅ OK: $proj_rel"
  fi
  rc=$((rc + proj_errors))
done < <(find "$REPO" -name '*.csproj' -not -path '*/.git/*' -not -path '*/obj/*' -not -path '*/bin/*' -print0 2>/dev/null)

echo
if [ "$rc" -eq 0 ]; then
  echo "✅ Todas as convenções validadas com sucesso."
else
  echo "❌ $rc problema(s) encontrado(s). Corrija antes de commitar."
fi

exit "$rc"
