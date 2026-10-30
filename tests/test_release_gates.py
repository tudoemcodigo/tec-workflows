# --------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Roberto Oliveira / Tudo em Código.
# Autor: Roberto Oliveira | Criação: 2026-10-24
# Licenciado sob a Licença Apache, Versão 2.0. Consulte LICENSE e NOTICE na raiz.
# --------------------------------------------------------------------------------------------------------------------

"""Testes dos portões de publicação em actions/release-gates/release_gates.py."""

import sys
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
from subprocess import CalledProcessError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "actions" / "release-gates"))
import release_gates  # noqa: E402


class TestReleaseGates(unittest.TestCase):
    def check(self, status: str = "completed", conclusion: str = "success") -> dict:
        return {
            "id": 42,
            "name": "ci / ci-ok",
            "started_at": "2026-10-24T12:00:00Z",
            "status": status,
            "conclusion": conclusion,
            "app": {"slug": "github-actions"},
        }

    def test_open_pull_request_blocks_release(self) -> None:
        error = release_gates.validate_release_gates([{"number": 17}], [self.check()])
        self.assertIn("17", error or "")

    def test_missing_ci_ok_blocks_release(self) -> None:
        error = release_gates.validate_release_gates([], [])
        self.assertIn("ci-ok", error or "")

    def test_latest_ci_ok_must_be_completed_successfully(self) -> None:
        older_success = self.check()
        newer_failure = {**self.check(conclusion="failure"), "id": 43, "started_at": "2026-10-24T13:00:00Z"}
        error = release_gates.validate_release_gates([], [older_success, newer_failure])
        self.assertIsNotNone(error)

    def test_successful_latest_ci_ok_allows_release(self) -> None:
        self.assertIsNone(release_gates.validate_release_gates([], [self.check()]))

    def test_ci_ok_from_another_app_blocks_release(self) -> None:
        impostor = {**self.check(), "app": {"slug": "app-de-terceiro"}}
        error = release_gates.validate_release_gates([], [impostor])
        self.assertIn("GitHub Actions", error or "")

    def test_ci_ok_without_app_blocks_release(self) -> None:
        no_app = self.check()
        del no_app["app"]
        self.assertIsNotNone(release_gates.validate_release_gates([], [no_app]))

    def test_ci_ok_with_malformed_app_blocks_release(self) -> None:
        for app in (None, "github-actions", {}, {"slug": None}, {"slug": "GitHub-Actions"}):
            with self.subTest(app=app):
                malformed = {**self.check(), "app": app}
                self.assertIsNotNone(release_gates.validate_release_gates([], [malformed]))

    def test_newer_ci_ok_from_another_app_does_not_override_actions_result(self) -> None:
        # O resultado que vale é o do Actions: um check mais novo de outro app não aprova nem reprova
        actions_failure = self.check(conclusion="failure")
        impostor_success = {
            **self.check(),
            "id": 99,
            "started_at": "2026-10-24T14:00:00Z",
            "app": {"slug": "app-de-terceiro"},
        }
        self.assertIsNotNone(release_gates.validate_release_gates([], [actions_failure, impostor_success]))

    def test_explicit_override_allows_open_prs_but_still_requires_ci_ok(self) -> None:
        prs = [{"number": 17}]
        self.assertIsNone(release_gates.validate_release_gates(prs, [self.check()], allow_open_prs=True))
        self.assertIsNotNone(release_gates.validate_release_gates(prs, [], allow_open_prs=True))

    @patch.dict("os.environ", {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_SHA": "abc123", "ALLOW_OPEN_PRS": "true"})
    @patch("release_gates.subprocess.run", side_effect=CalledProcessError(1, "gh"))
    def test_github_api_failure_blocks_release(self, _run_gh: object) -> None:
        output = StringIO()
        with redirect_stdout(output):
            result = release_gates.main()
        self.assertEqual(result, 2)
        self.assertIn("Não foi possível validar", output.getvalue())


if __name__ == "__main__":
    unittest.main()
