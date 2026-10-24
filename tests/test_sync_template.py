# --------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Roberto Oliveira / Tudo em Código.
# Autor: Roberto Oliveira | Criação: 2026-10-24
# Licenciado sob a Licença Apache, Versão 2.0. Consulte LICENSE e NOTICE na raiz.
# --------------------------------------------------------------------------------------------------------------------

"""Testes do contrato de sincronização: scripts/sync-template.sh."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestSyncTemplate(unittest.TestCase):
    def setUp(self) -> None:
        if os.name == "nt":
            self.skipTest("o script usa Bash e é executado no CI Ubuntu")
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "TEC.Test"
        self.repo.mkdir()
        self.script = Path(__file__).resolve().parent.parent / "scripts" / "sync-template.sh"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def sync(self) -> None:
        subprocess.run(["bash", str(self.script), str(self.repo)], check=True, capture_output=True, text=True)

    def test_existing_readme_and_changelog_are_preserved(self) -> None:
        readme = self.repo / "README.md"
        changelog = self.repo / "CHANGELOG.md"
        readme.write_text("# TEC.Test específico\n", encoding="utf-8")
        changelog.write_text("# TEC.Test 0.0.1\n", encoding="utf-8")

        self.sync()

        self.assertEqual(readme.read_text(encoding="utf-8"), "# TEC.Test específico\n")
        self.assertEqual(changelog.read_text(encoding="utf-8"), "# TEC.Test 0.0.1\n")
        self.assertTrue((self.repo / ".editorconfig").is_file())

    def test_missing_readme_and_changelog_receive_starters(self) -> None:
        self.sync()

        readme = (self.repo / "README.md").read_text(encoding="utf-8")
        self.assertIn("tudoemcodigo-icone-512.png", readme)
        self.assertIn("TEC.X", readme)
        self.assertTrue((self.repo / "CHANGELOG.md").is_file())


if __name__ == "__main__":
    unittest.main()
