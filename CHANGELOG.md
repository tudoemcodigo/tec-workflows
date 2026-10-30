# CHANGELOG.md

Sequência de versões do repositório `tec-workflows`.

## [1.0.0] - 2026-10-30

### Adicionado
- Primeira publicação dos workflows reutilizáveis, composite actions, arquivos canônicos de build e documentação.
- Portões de segurança para release e validação local de convenções.
- Alvo único `net10.0`: o `build/Tec.Build.props` define `TargetFrameworks` como `net10.0`; CI, release, testes e
  benchmarks instalam só o SDK do `global.json` (a entrada `runtimes` de `actions/setup-dotnet` tem padrão vazio).
- **Dependabot do template**: ASP.NET Core e EF Core recebem minor e patch; as majors desses pacotes e de
  `Microsoft.Extensions.DependencyInjection*`/`*.Abstractions` ficam ignoradas (sobem com um alvo novo).
- **README do template**: links absolutos para `https://github.com/tudoemcodigo/lib-tec-x/blob/main/...`, porque o
  README vai dentro do pacote NuGet.

### Segurança
- **Portões de publicação**: chamadas à API do GitHub que falham ou não encontram `ci-ok` bloqueiam o release, e o
  `ci-ok` só conta se o check run vier do GitHub Actions (`app.slug` igual a `github-actions`). Check com o mesmo nome
  criado por outro GitHub App, ou sem o campo `app`, não libera o release.
- **Relatório de testes**: carregamento dos testes, extração do TFM e escape de dados não confiáveis no resumo.
- **Aprovação do release**: o mesmo environment protege a criação da tag/Release e a publicação no feed; o atestado é
  gerado antes da criação da Release.

Veja as versões e notas nas [Releases do GitHub](https://github.com/tudoemcodigo/tec-workflows/releases).
