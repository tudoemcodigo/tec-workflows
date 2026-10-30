# --------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Roberto Oliveira / Tudo em Código.
# Autor: Roberto Oliveira | Criação: 2026-10-24
# Licenciado sob a Licença Apache, Versão 2.0. Consulte LICENSE e NOTICE na raiz.
# --------------------------------------------------------------------------------------------------------------------

"""Fail-closed validation for the reusable release workflow's GitHub gates."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

# Só o GitHub Actions publica o ci-ok. Qualquer GitHub App com checks: write consegue criar um check run com o mesmo
# nome; sem conferir a origem, ele bastaria para liberar a publicação.
CI_OK_APP_SLUG = "github-actions"


def _is_ci_ok(check: dict[str, Any]) -> bool:
    name = check.get("name")
    if not isinstance(name, str) or not (name == "ci-ok" or name.endswith(" / ci-ok")):
        return False
    app = check.get("app")
    # Sem o campo app (ou com outro formato) o check não conta: falha fechada
    return isinstance(app, dict) and app.get("slug") == CI_OK_APP_SLUG


def validate_release_gates(
    open_prs: list[dict[str, Any]], check_runs: list[dict[str, Any]], *, allow_open_prs: bool = False
) -> str | None:
    """Return a user-safe error unless main has no open PRs and its newest GitHub Actions ci-ok passed."""
    if open_prs and not allow_open_prs:
        numbers = [str(pr.get("number", "?")) if isinstance(pr.get("number"), int) else "?" for pr in open_prs]
        return "Há PR(s) aberto(s) visando a main: " + ", ".join(numbers)

    ci_checks = [check for check in check_runs if isinstance(check, dict) and _is_ci_ok(check)]
    if not ci_checks:
        return "O commit não possui um check ci-ok do GitHub Actions; publicação bloqueada."

    latest = max(ci_checks, key=lambda item: (item.get("started_at") or "", int(item.get("id", 0))))
    if latest.get("status") != "completed" or latest.get("conclusion") != "success":
        return "O check ci-ok mais recente não terminou com sucesso; publicação bloqueada."
    return None


def _gh(args: list[str]) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    sha = os.environ.get("GITHUB_SHA", "")
    if not repo or not sha:
        print("::error::GITHUB_REPOSITORY e GITHUB_SHA são obrigatórios.")
        return 2

    allow_open_prs = os.environ.get("ALLOW_OPEN_PRS", "false").lower() == "true"
    try:
        prs = []
        if not allow_open_prs:
            prs = json.loads(
                _gh(["pr", "list", "--repo", repo, "--base", "main", "--state", "open", "--json", "number"])
            )
        raw_checks = _gh(
            [
                "api",
                "--paginate",
                "--jq",
                ".check_runs[] | @json",
                f"repos/{repo}/commits/{sha}/check-runs?per_page=100",
            ]
        )
        check_runs = [json.loads(line) for line in raw_checks.splitlines() if line.strip()]
        if not isinstance(prs, list):
            raise ValueError("A resposta da consulta de PRs não é uma lista.")
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError, ValueError):
        print("::error::Não foi possível validar os portões de publicação pela API do GitHub.")
        return 2

    error = validate_release_gates(prs, check_runs, allow_open_prs=allow_open_prs)
    if error:
        print(f"::error::{error}")
        return 1
    print("Portões de release aprovados: nenhum PR aberto e ci-ok mais recente com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
