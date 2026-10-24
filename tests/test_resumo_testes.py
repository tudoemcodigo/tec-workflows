# --------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Roberto Oliveira / Tudo em Código.
# Autor: Roberto Oliveira | Criação: 2026-10-24
# Licenciado sob a Licença Apache, Versão 2.0. Consulte LICENSE e NOTICE na raiz.
# --------------------------------------------------------------------------------------------------------------------

"""Testes do actions/test-summary/resumo-testes.py: python3 -m unittest discover -s tests"""

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

CAMINHO = Path(__file__).resolve().parent.parent / "actions" / "test-summary" / "resumo-testes.py"
spec = importlib.util.spec_from_file_location("resumo_testes", CAMINHO)
assert spec is not None and spec.loader is not None
resumo_testes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resumo_testes)

TRX_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<TestRun id="run1" name="test" runUser="user" xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010">
  <TestDefinitions>
    <UnitTest id="ut1" name="Test1" storage="net8.0/Test1.dll" />
    <UnitTest id="ut2" name="Test2" storage="net8.0/Test2.dll" />
    <UnitTest id="ut3" name="Test3" storage="net10.0/Test3.dll" />
  </TestDefinitions>
  <Results>
    <UnitTestResult testId="ut1" testName="Test1" outcome="Passed" />
    <UnitTestResult testId="ut2" testName="Test2" outcome="Failed" />
    <UnitTestResult testId="ut3" testName="Test3" outcome="NotExecuted">
      <Output>
        <DebugTrace>Skipped: Sem acesso ao Vault</DebugTrace>
      </Output>
    </UnitTestResult>
  </Results>
</TestRun>
"""

TRX_TEMPLATE_2 = """<?xml version="1.0" encoding="utf-8"?>
<TestRun id="run2" name="test2" runUser="user" xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010">
  <TestDefinitions>
    <UnitTest id="ut1" name="Test1" storage="net8.0/Test1.dll" />
    <UnitTest id="ut3" name="Test3" storage="net10.0/Test3.dll" />
  </TestDefinitions>
  <Results>
    <UnitTestResult testId="ut1" testName="Test1" outcome="Passed" />
    <UnitTestResult testId="ut3" testName="Test3" outcome="Passed" />
  </Results>
</TestRun>
"""

TRX_MALFORMED = """<?xml version="1.0" encoding="utf-8"?>
<TestRun id="run3" name="test3" runUser="user" xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010">
  <TestDefinitions>
    <UnitTest id="ut4" name="Test4" storage="net8.0/Test4.dll" />
  </TestDefinitions>
  <Results>
    <UnitTestResult testId="ut4" testName="Test4" outcome="Passed" />
  </Results>
</TestRun
"""


class TestResumoTestes(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_trx(self, name: str, content: str) -> Path:
        p = self.dir / name
        p.write_text(content, encoding="utf-8")
        return p

    def run_script(self, *args: str) -> str:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = resumo_testes.main([*args, str(self.dir), str(self.dir / "summary.md")])
            self.assertEqual(rc, 0)
        return out.getvalue()

    def test_single_trx_counts(self) -> None:
        self.write_trx("a.trx", TRX_TEMPLATE)
        out = self.run_script()
        self.assertIn("| 3 | 1 | 1 | 1 |", out)
        self.assertIn("❌ Falhas (1)", out)
        self.assertIn("Test2", out)
        self.assertIn("⏭️ Pulados (1)", out)
        self.assertIn("Sem acesso ao Vault", out)

    def test_priority_merge_failed_over_passed(self) -> None:
        # Mesmo teste aparece em dois .trx: Failed em um, Passed no outro -> Failed vence
        self.write_trx("build.trx", TRX_TEMPLATE)
        self.write_trx("integration.trx", TRX_TEMPLATE_2)
        out = self.run_script()
        # Test1: Passed + Passed = Passed
        # Test2: Failed (só no build) = Failed
        # Test3: NotExecuted (build) + Passed (integration) = Passed
        self.assertIn("| 3 | 2 | 1 | 0 |", out)

    def test_priority_merge_passed_over_not_executed(self) -> None:
        # Test3: NotExecuted no build, Passed na integration -> Passed vence
        self.write_trx("build.trx", TRX_TEMPLATE)
        self.write_trx("integration.trx", TRX_TEMPLATE_2)
        out = self.run_script()
        self.assertIn("| 3 | 2 | 1 | 0 |", out)

    def test_ignore_pattern(self) -> None:
        self.write_trx("TEC.Core.LoadTests.trx", TRX_TEMPLATE)
        self.write_trx("TEC.Core.Tests.trx", TRX_TEMPLATE_2)
        out = self.run_script("--ignorar", "TEC.Core.LoadTests*")
        # Só o segundo arquivo conta (2 testes)
        self.assertIn("| 2 | 2 | 0 | 0 |", out)

    def test_malformed_trx_warning(self) -> None:
        self.write_trx("good.trx", TRX_TEMPLATE)
        self.write_trx("bad.trx", TRX_MALFORMED)
        out = self.run_script()
        self.assertIn("⚠️ 1 arquivo(s) .trx ilegível(is)", out)
        self.assertIn("bad.trx", out)

    def test_tfm_extraction(self) -> None:
        self.assertEqual(resumo_testes.alvo("net8.0/MyTest.dll"), "net8.0")
        self.assertEqual(resumo_testes.alvo("/src/bin/Release/net8.0/MyTest.dll"), "net8.0")
        self.assertEqual(resumo_testes.alvo("net10.0/MyTest.dll"), "net10.0")
        self.assertEqual(resumo_testes.alvo("something/net6.0/other.dll"), "net6.0")
        self.assertEqual(resumo_testes.alvo("no-tfm-here.dll"), "?")
        self.assertEqual(resumo_testes.alvo(""), "?")

    def test_untrusted_names_are_escaped_in_markdown(self) -> None:
        malicious = TRX_TEMPLATE.replace('testName="Test2"', 'testName="&lt;script&gt;|bad`name`&#10;next"')
        self.write_trx("a.trx", malicious)
        out = self.run_script()
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertNotIn("|bad`name`", out)

    def test_outcome_normalization(self) -> None:
        # Error, Timeout, Aborted viram Failed
        for o in ("Error", "Timeout", "Aborted"):
            self.assertEqual(resumo_testes.PRIORIDADE.get(o, 3), 3)
        # Unknown vira NotExecuted (prioridade 1)
        self.assertEqual(resumo_testes.PRIORIDADE.get("Unknown", 1), 1)


if __name__ == "__main__":
    unittest.main()
