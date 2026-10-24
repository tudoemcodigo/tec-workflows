# --------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Roberto Oliveira / Tudo em Código.
# Autor: Roberto Oliveira | Criação: 2026-10-24
# Licenciado sob a Licença Apache, Versão 2.0. Consulte LICENSE e NOTICE na raiz.
# --------------------------------------------------------------------------------------------------------------------

"""Testes do actions/versao/versao.py: python3 -m unittest discover -s tests"""

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "actions" / "versao"))
import versao  # noqa: E402

PROPS = "<Project>\n  <PropertyGroup>\n    <Version>{0}</Version>\n  </PropertyGroup>\n</Project>\n"


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.props = self.dir / "Directory.Build.props"
        self.tags = self.dir / "tags.txt"
        self.tags.write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def com(self, version: str, *tags: str) -> None:
        self.props.write_text(PROPS.format(version), encoding="utf-8")
        self.tags.write_text("".join(f"refs/tags/{t}\n" for t in tags), encoding="utf-8")

    def rodar(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            try:
                rc = versao.main([*args, "--props", str(self.props), "--tags", str(self.tags)])
            except SystemExit as e:
                rc = e.code
        return rc, out.getvalue()


class OrdemSemVer(unittest.TestCase):
    def test_ordem(self) -> None:
        ordem = ["0.0.1", "0.1.0-ci.5", "0.1.0-preview.2", "0.1.0-preview.10", "0.1.0-rc.1", "0.1.0-rc.2",
                 "0.1.0-rc.10", "0.1.0", "0.1.1", "0.2.0", "1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta",
                 "1.0.0-beta.2", "1.0.0-beta.11", "1.0.0", "10.0.0"]
        self.assertEqual(sorted(reversed(ordem), key=versao.chave), ordem)

    def test_invalida(self) -> None:
        for v in ("1.0", "01.0.0", "1.0.0-", "v1.0.0", "1.0.0.0"):
            self.assertIsNone(versao.chave(v), v)


class Release(Base):
    def test_valida(self) -> None:
        casos = [
            ("0.2.0", ["v0.1.0", "v0.0.1"], "0.2.0"),
            ("0.2.0", ["v0.1.0"], "v0.2.0-rc.1"),        # 'v' inicial aceito
            ("0.2.0", ["v0.2.0-rc.1", "v0.1.0"], "0.2.0"),  # estável depois do rc
            ("0.2.0", ["v0.2.0-rc.1"], "0.2.0-rc.2"),
            ("0.2.0", ["v0.2.0-rc.9"], "0.2.0-rc.10"),    # numérico, não texto
            ("0.0.1", [], "0.0.1"),                       # primeira publicação
            ("1.0.0", ["v0.9.0", "nao-semver", "vX"], "1.0.0"),
        ]
        for base, tags, digitada in casos:
            with self.subTest(base=base, digitada=digitada):
                self.com(base, *tags)
                rc, out = self.rodar("release", "--versao", digitada)
                self.assertEqual(rc, 0, out)
                self.assertIn(f"version={digitada.removeprefix('v')}\npublish=true", out)

    def test_recusa(self) -> None:
        casos = [
            ("0.1.0", [], "0.2.0", "não corresponde"),            # M3: diferente da <Version>
            ("0.1.0", [], "0.0.5", "não corresponde"),
            ("0.1.0", ["v0.1.0"], "0.1.0", "já existe"),
            ("0.1.0", ["v0.2.0"], "0.1.0", "não é maior"),        # abaixo da última lançada
            ("0.1.0", ["v0.1.0"], "0.1.0-rc.1", "não é maior"),   # rc depois da estável
            ("0.1.0", ["v0.1.0-rc.2"], "0.1.0-rc.1", "não é maior"),
            ("0.1.0", [], "0.1.0-rcX1", "padrão"),                # B2: ponto sem escape
            ("0.1.0", [], "0.1.0-rc-1", "padrão"),
            ("0.1.0", [], "0.1.0-rc.0", "padrão"),
            ("0.1.0", [], "0.1.0-preview.1", "padrão"),           # prévias só pelo CI
            ("0.1.0", [], "0.1", "padrão"),
            ("0.1.0", [], "0.1.0; rm -rf /", "padrão"),
            ("0.1", [], "0.1.0", "fora do padrão"),               # <Version> inválida
        ]
        for base, tags, digitada, msg in casos:
            with self.subTest(base=base, tags=tags, digitada=digitada):
                self.com(base, *tags)
                rc, out = self.rodar("release", "--versao", digitada)
                self.assertEqual(rc, 1, out)
                self.assertIn("::error::", out)
                self.assertIn(msg, out)


class Ci(Base):
    def setUp(self) -> None:
        super().setUp()
        self.cwd = os.getcwd()
        git(self.dir, "init", "-q", "-b", "main")
        git(self.dir, "config", "user.email", "t@t")
        git(self.dir, "config", "user.name", "t")
        os.chdir(self.dir)

    def tearDown(self) -> None:
        os.chdir(self.cwd)
        super().tearDown()

    def commit(self, version: str | None = None) -> None:
        if version is not None:
            self.props.write_text(PROPS.format(version), encoding="utf-8")
        else:
            (self.dir / "x.txt").write_text(str(os.urandom(4)), encoding="utf-8")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "c")

    def tags_(self, *tags: str) -> None:
        self.tags.write_text("".join(f"refs/tags/{t}\n" for t in tags), encoding="utf-8")

    def previa(self) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = versao.main(["ci", "--props", "Directory.Build.props", "--tags", str(self.tags), "--previa", "true"])
        return rc, out.getvalue()

    def test_fora_da_main(self) -> None:
        self.commit("0.2.0")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            versao.main(["ci", "--props", "Directory.Build.props", "--previa", "false", "--run", "42"])
        self.assertIn("version=0.2.0-ci.42\npublish=false", out.getvalue())

    def test_fora_da_main_com_versao_ja_lancada(self) -> None:
        self.commit("0.2.0")
        self.tags_("v0.2.0")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            versao.main(["ci", "--props", "Directory.Build.props", "--tags", str(self.tags), "--previa", "false", "--run", "42"])
        texto = out.getvalue()
        self.assertIn("::warning::", texto)
        self.assertIn("já foi lançada", texto)
        self.assertIn("version=0.2.0-ci.42\npublish=false", texto)

    def test_sequencia(self) -> None:
        self.commit("0.2.0")
        self.assertIn("version=0.2.0-preview.1\npublish=true", self.previa()[1])
        self.commit()
        self.commit()
        self.assertIn("version=0.2.0-preview.3\npublish=true", self.previa()[1])
        self.commit("0.3.0")
        self.assertIn("version=0.3.0-preview.1\npublish=true", self.previa()[1])

    def test_versao_ja_lancada(self) -> None:
        self.commit("0.2.0")
        self.tags_("v0.2.0")
        rc, out = self.previa()
        self.assertIn("::notice::", out)
        self.assertIn("version=0.2.0\npublish=false", out)

    def test_depois_do_rc(self) -> None:  # M3: preview < rc
        self.commit("0.2.0")
        self.tags_("v0.2.0-rc.1")
        rc, out = self.previa()
        self.assertIn("::warning::", out)
        self.assertIn("publish=false", out)

    def test_versao_maior_lancada(self) -> None:  # M3: 0.2.0 lançada com <Version> 0.1.0
        self.commit("0.1.0")
        self.tags_("v0.2.0", "v0.0.1")
        rc, out = self.previa()
        self.assertIn("::warning::", out)
        self.assertIn("publish=false", out)

    def test_revert_reinicia_sequencia(self) -> None:
        # M4: o revert reinicia a contagem; a colisão com prévias já publicadas é detectada no push (dotnet-ci.yml)
        self.commit("0.2.0")
        self.commit()
        self.commit("0.3.0")
        self.commit("0.2.0")
        self.assertIn("version=0.2.0-preview.1\npublish=true", self.previa()[1])


if __name__ == "__main__":
    unittest.main()
