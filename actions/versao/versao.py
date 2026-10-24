# --------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Roberto Oliveira / Tudo em Código.
# Autor: Roberto Oliveira | Criação: 2026-10-24
# Licenciado sob a Licença Apache, Versão 2.0. Consulte LICENSE e NOTICE na raiz.
# --------------------------------------------------------------------------------------------------------------------

"""Versão do componente: prévia do CI (push na main) e versão digitada no release.

Uso:
  python3 versao.py ci      --props Directory.Build.props --tags <arquivo> --previa true|false --run <N>
  python3 versao.py release --props Directory.Build.props --tags <arquivo> --versao <X.Y.Z ou X.Y.Z-rc.N>

--tags: arquivo com as tags do repositório, uma por linha ('v1.2.3' ou 'refs/tags/v1.2.3'); linhas fora do SemVer
são ignoradas. No modo ci, --tags só é lido com --previa true.

Saída: linhas 'version=...' e 'publish=...' (para o GITHUB_OUTPUT) no stdout; erros e avisos como comandos do
GitHub Actions (::error::, ::warning::, ::notice::). Código 1 em erro de validação.

Regras (comparação SemVer 2.0.0: 1.0.0-preview.9 < 1.0.0-preview.10 < 1.0.0-rc.1 < 1.0.0):
  release: formato X.Y.Z ou X.Y.Z-rc.N; X.Y.Z == <Version> do Directory.Build.props; a tag não existe; a versão é
           maior que todas as tags já lançadas.
  ci:      fora da prévia, <Version>-ci.<run>. Na prévia, <Version>-preview.N (N = commits da main desde o commit que
           definiu a <Version>, contando ele), publicada só se for maior que todas as tags (senão, ficaria abaixo de
           uma versão já lançada: a própria <Version>, um rc dela ou uma versão maior).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

NUCLEO = r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
SEMVER = re.compile(NUCLEO + r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z.-]+)?")
RELEASE = re.compile(NUCLEO + r"(-rc\.[1-9][0-9]*)?")
BASE = re.compile(NUCLEO)
VERSION_TAG = re.compile(r"<Version>\s*([^<]*?)\s*</Version>")


def chave(versao: str) -> tuple | None:
    """Chave de ordenação SemVer 2.0.0 (None se não for SemVer)."""
    m = SEMVER.fullmatch(versao)
    if not m:
        return None
    nucleo = tuple(int(m.group(i)) for i in (1, 2, 3))
    pre = m.group(4)
    if pre is None:
        return nucleo, (1,)  # estável vem depois de qualquer pré-versão do mesmo núcleo
    ids = []
    for ident in pre.split("."):
        # numérico < alfanumérico; numéricos por valor; alfanuméricos em ASCII
        ids.append((0, int(ident), "") if ident.isdigit() else (1, 0, ident))
    # Mais identificadores (com o mesmo prefixo) ordena depois: a tupla do Python já faz isso
    return nucleo, (0, tuple(ids))


def ler_tags(arquivo: Path) -> list[str]:
    tags = []
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        nome = linha.strip().removeprefix("refs/tags/")
        if nome.startswith("v") and chave(nome[1:]) is not None:
            tags.append(nome[1:])
    return tags


def maior(versoes: list[str]) -> str | None:
    return max(versoes, key=chave) if versoes else None


def ler_base(props: Path) -> str:
    m = VERSION_TAG.search(props.read_text(encoding="utf-8")) if props.is_file() else None
    base = m.group(1) if m else ""
    if not BASE.fullmatch(base):
        erro(f"<Version> do {props} ausente ou fora do padrão X.Y.Z (atual: '{base}').")
    return base


def erro(msg: str) -> None:
    print(f"::error::{msg}")
    sys.exit(1)


def sequencia(props: Path) -> int:
    """Commits da main (--first-parent) desde o último que alterou uma linha com <Version>, contando ele."""
    git = ["git", "log", "--first-parent", "-1", "--format=%H", "-G<Version>", "--", str(props)]
    since = subprocess.run(git, check=True, capture_output=True, text=True).stdout.strip()
    if not since:
        erro(f"Nenhum commit da main definiu a <Version> do {props}.")
    conta = ["git", "rev-list", "--count", "--first-parent", f"{since}..HEAD"]
    return int(subprocess.run(conta, check=True, capture_output=True, text=True).stdout.strip()) + 1


def modo_release(a: argparse.Namespace) -> tuple[str, bool]:
    bruta = a.versao.strip()
    versao = bruta.removeprefix("v")
    if not RELEASE.fullmatch(versao):
        erro(f"A versão '{bruta}' não segue o padrão X.Y.Z ou X.Y.Z-rc.N (prévias saem do CI a cada push na main).")
    base = ler_base(a.props)
    nucleo = versao.split("-", 1)[0]
    if nucleo != base:
        erro(
            f"A versão {versao} não corresponde à <Version> {base} do {a.props}: publique {base} (ou {base}-rc.N) "
            f"ou ajuste a <Version> num PR antes."
        )
    tags = ler_tags(a.tags)
    if versao in tags:
        erro(f"A tag v{versao} já existe.")
    ultima = maior(tags)
    if ultima is not None and chave(versao) <= chave(ultima):
        erro(f"A versão {versao} não é maior que a última lançada (v{ultima}). Suba a <Version> do {a.props}.")
    return versao, True


def modo_ci(a: argparse.Namespace) -> tuple[str, bool]:
    base = ler_base(a.props)
    tags = ler_tags(a.tags) if a.tags and a.tags.is_file() else []
    if a.previa != "true":
        if base in tags:
            print(
                f"::warning::A versão base {base} do {a.props} já foi lançada (tag v{base}). "
                "Para que este PR gere novas prévias após o merge ou possa ser lançado no release, "
                "incremente a <Version> do Directory.Build.props."
            )
        return f"{base}-ci.{a.run}", False
    if base in tags:
        # Versão já lançada e mantida de propósito (ex.: só ajustes de build ou documentação): valida tudo, sem prévia
        print(
            f"::notice::A versão {base} já foi publicada (tag v{base}): nenhuma prévia gerada. Para publicar novas "
            "prévias, suba a <Version> do Directory.Build.props."
        )
        return base, False
    versao = f"{base}-preview.{sequencia(a.props)}"
    ultima = maior(tags)
    if ultima is not None and chave(versao) <= chave(ultima):
        # Ex.: v<Version>-rc.1 já lançada (preview < rc) ou uma versão maior que a <Version> já lançada
        print(
            f"::warning::A prévia {versao} ficaria abaixo da última versão lançada (v{ultima}) e não seria "
            "oferecida a quem usa faixa flutuante: nenhuma prévia gerada. Suba a <Version> do Directory.Build.props."
        )
        return base, False
    return versao, True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("modo", choices=["ci", "release"])
    p.add_argument("--props", type=Path, default=Path("Directory.Build.props"))
    p.add_argument("--tags", type=Path)
    p.add_argument("--previa", default="false")
    p.add_argument("--run", default="0")
    p.add_argument("--versao", default="")
    a = p.parse_args(argv)
    if (a.modo == "release" or a.previa == "true") and a.tags is None:
        p.error("--tags é obrigatório no release e na prévia")
    versao, publicar = modo_release(a) if a.modo == "release" else modo_ci(a)
    print(f"version={versao}")
    print(f"publish={'true' if publicar else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
