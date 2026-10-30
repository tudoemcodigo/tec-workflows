# --------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Roberto Oliveira / Tudo em Código.
# Autor: Roberto Oliveira | Criação: 2026-10-24
# Licenciado sob a Licença Apache, Versão 2.0. Consulte LICENSE e NOTICE na raiz.
# --------------------------------------------------------------------------------------------------------------------

"""Testes da action check-conventions: python3 -m unittest discover -s tests"""

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestCheckConventions(unittest.TestCase):
    def setUp(self) -> None:
        if os.name == "nt":
            self.skipTest("estes testes reproduzem etapas Bash do GitHub Actions e são executados em Ubuntu")
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.template = Path(__file__).resolve().parent.parent / "template"
        self.action = Path(__file__).resolve().parent.parent / "actions" / "check-conventions" / "action.yml"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_check(self, repo: Path | None = None) -> tuple[int, str]:
        repo = repo or self.repo
        # Simula o step "Arquivos canônicos" do action.yml
        rc = 0
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            try:
                # Arquivos canônicos
                proc = subprocess.run(
                    ["bash", "-c", f"""
set -euo pipefail
TEMPLATE="{self.template}"
rc=0
while IFS= read -r -d '' file; do
  rel="${{file#./}}"
  if [ ! -f "{repo}/$rel" ]; then
    echo "::error file=$rel::Arquivo canônico ausente (rode scripts/sync-template.sh do tec-workflows)."
    rc=1
  elif [[ "$rel" == "README.md" || "$rel" == "CHANGELOG.md" ]]; then
    continue
  elif ! cmp -s "$TEMPLATE/$rel" "{repo}/$rel"; then
    echo "::error file=$rel::Diverge do template do tec-workflows (edite lá e rode scripts/sync-template.sh)."
    rc=1
  fi
done < <(cd "$TEMPLATE" && find . -type f -print0)
while IFS= read -r -d '' readme; do
  if ! grep -Fq 'tudoemcodigo-icone-512.png' "$readme"; then
    echo "::error file=$readme::README sem a marca Tudo em Código."
    rc=1
  fi
done < <(find "{repo}" -name README.md -not -path '*/.git/*' -not -path '*/obj/*' -not -path '*/bin/*' -print0)
exit "$rc"
"""],
                    capture_output=True,
                    text=True,
                )
                out.write(proc.stdout)
                out.write(proc.stderr)
                if proc.returncode != 0:
                    rc = 1

                # NOTICE
                if not (repo / "NOTICE").exists():
                    out.write("::error file=NOTICE::Arquivo NOTICE de atribuição exigido pela convenção TEC ausente na raiz do repositório.\n")
                    rc = 1

                # Convenções dos projetos
                proj_rc = subprocess.run(
                    ["bash", "-c", f"""
set -euo pipefail
rc=0
cd "{repo}"
while IFS= read -r -d '' proj; do
  if grep -Eq '<PackageReference[^>]+Version=' "$proj" || grep -Eq 'VersionOverride=' "$proj"; then
    echo "::error file=$proj::PackageReference com Version ou VersionOverride: declare a versão no Directory.Packages.props."
    rc=1
  fi
  if grep -Eq '<PackageReference[^>]+Include="TEC\\.' "$proj"; then
    echo "::error file=$proj::Componente TEC.* via PackageReference: use <TecReference Include=\\"TEC.X\\" />."
    rc=1
  fi
  if grep -Eq '<(Version|PackageVersion|VersionPrefix|VersionSuffix)>' "$proj"; then
    echo "::error file=$proj::Versão no csproj (<Version>, <PackageVersion>, <VersionPrefix>, <VersionSuffix>): a versão é única por repositório (Directory.Build.props)."
    rc=1
  fi
done < <(find . -name '*.csproj' -not -path './.git/*' -print0)

exit "$rc"
"""],
                    capture_output=True,
                    text=True,
                )
                out.write(proj_rc.stdout)
                out.write(proj_rc.stderr)
                if proj_rc.returncode != 0:
                    rc = max(rc, 1)
            except Exception as e:
                out.write(str(e))
                rc = 1
        return rc, out.getvalue()

    def create_minimal_repo(self) -> None:
        # Copia arquivos canônicos essenciais
        for f in self.template.rglob("*"):
            if f.is_file():
                rel = f.relative_to(self.template)
                target = self.repo / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)
        # Cria csproj de exemplo válido
        csproj = self.repo / "TEC.Test" / "TEC.Test.csproj"
        csproj.parent.mkdir(parents=True, exist_ok=True)
        csproj.write_text("""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFrameworks>net10.0</TargetFrameworks>
  </PropertyGroup>
  <ItemGroup>
    <TecReference Include="TEC.Core" />
  </ItemGroup>
</Project>
""", encoding="utf-8")
        # Directory.Packages.props válido
        dpp = self.repo / "Directory.Packages.props"
        dpp.write_text("""<Project>
  <ItemGroup>
    <PackageVersion Include="Microsoft.Extensions.DependencyInjection">10.0.12</PackageVersion>
    <PackageVersion Include="TEC.Core">0.0.1</PackageVersion>
  </ItemGroup>
</Project>
""", encoding="utf-8")

    def test_valid_repo_passes(self) -> None:
        self.create_minimal_repo()
        rc, out = self.run_check()
        self.assertEqual(rc, 0, out)
        self.assertNotIn("::error", out)

    def test_missing_canonical_file_fails(self) -> None:
        self.create_minimal_repo()
        (self.repo / ".editorconfig").unlink()
        rc, out = self.run_check()
        self.assertEqual(rc, 1)
        self.assertIn("Arquivo canônico ausente", out)

    def test_divergent_canonical_file_fails(self) -> None:
        self.create_minimal_repo()
        (self.repo / ".editorconfig").write_text("# modificado\n", encoding="utf-8")
        rc, out = self.run_check()
        self.assertEqual(rc, 1)
        self.assertIn("Diverge do template", out)

    def test_component_readme_and_changelog_can_be_customized(self) -> None:
        self.create_minimal_repo()
        (self.repo / "README.md").write_text(
            '<img src="https://www.tudoemcodigo.com/marca/PNG/tudoemcodigo-icone-512.png" alt="Tudo em Código">\n# TEC.Core\n',
            encoding="utf-8",
        )
        (self.repo / "CHANGELOG.md").write_text("# TEC.Core 0.0.1\n", encoding="utf-8")
        rc, out = self.run_check()
        self.assertEqual(rc, 0, out)

    def test_readme_without_brand_logo_fails(self) -> None:
        self.create_minimal_repo()
        (self.repo / "README.md").write_text("# TEC.Test\n", encoding="utf-8")
        rc, out = self.run_check()
        self.assertEqual(rc, 1)
        self.assertIn("README sem a marca Tudo em Código", out)

    def test_missing_notice_fails(self) -> None:
        self.create_minimal_repo()
        (self.repo / "NOTICE").unlink()
        rc, out = self.run_check()
        self.assertEqual(rc, 1)
        self.assertIn("NOTICE de atribuição", out)

    def test_package_reference_with_version_fails(self) -> None:
        self.create_minimal_repo()
        csproj = self.repo / "TEC.Test" / "TEC.Test.csproj"
        csproj.write_text("""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFrameworks>net10.0</TargetFrameworks>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
  </ItemGroup>
</Project>
""", encoding="utf-8")
        rc, out = self.run_check()
        self.assertEqual(rc, 1)
        self.assertIn("PackageReference com Version", out)

    def test_tec_via_package_reference_fails(self) -> None:
        self.create_minimal_repo()
        csproj = self.repo / "TEC.Test" / "TEC.Test.csproj"
        csproj.write_text("""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFrameworks>net10.0</TargetFrameworks>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="TEC.Core" Version="0.0.1" />
  </ItemGroup>
</Project>
""", encoding="utf-8")
        rc, out = self.run_check()
        self.assertEqual(rc, 1)
        self.assertIn("Componente TEC.* via PackageReference", out)

    def test_version_in_csproj_fails(self) -> None:
        self.create_minimal_repo()
        csproj = self.repo / "TEC.Test" / "TEC.Test.csproj"
        csproj.write_text("""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFrameworks>net10.0</TargetFrameworks>
    <Version>1.0.0</Version>
  </PropertyGroup>
  <ItemGroup>
    <TecReference Include="TEC.Core" />
  </ItemGroup>
</Project>
""", encoding="utf-8")
        rc, out = self.run_check()
        self.assertEqual(rc, 1)
        self.assertIn("Versão no csproj", out)

    def test_central_package_management_versions_are_accepted(self) -> None:
        # Version no Directory.Packages.props é o lugar certo: a regra de PackageReference com Version vale só no csproj
        self.create_minimal_repo()
        dpp = self.repo / "Directory.Packages.props"
        dpp.write_text("""<Project>
  <ItemGroup>
    <PackageVersion Include="Microsoft.Extensions.DependencyInjection" Version="10.0.12" />
  </ItemGroup>
</Project>
""", encoding="utf-8")
        rc, out = self.run_check()
        self.assertEqual(rc, 0, out)


if __name__ == "__main__":
    unittest.main()
