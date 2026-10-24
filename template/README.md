<div align="center">

<img src="https://www.tudoemcodigo.com/marca/PNG/tudoemcodigo-icone-512.png" alt="Tudo em Código" width="120" />

[🏠 Tudo em Código](https://github.com/tudoemcodigo) › [📦 TEC.X](https://github.com/tudoemcodigo/TEC.X)

# TEC.X

> Breve descrição do valor do componente: o problema que resolve e para quem.

[![CI](https://github.com/tudoemcodigo/TEC.X/actions/workflows/ci.yml/badge.svg)](https://github.com/tudoemcodigo/TEC.X/actions/workflows/ci.yml)
[![.NET](https://img.shields.io/badge/.NET-8.0%20%7C%2010.0-512BD4?logo=dotnet&logoColor=white)](docs/compatibilidade.md)
[![Native AOT](https://img.shields.io/badge/Native%20AOT-compat%C3%ADvel-512BD4)](docs/compatibilidade.md)
[![Versão](https://img.shields.io/badge/vers%C3%A3o-0.0.1-blue)](CHANGELOG.md)
[![NuGet](https://img.shields.io/badge/nuget-GitHub%20Packages-0969da?logo=github)](https://github.com/orgs/tudoemcodigo/packages)
[![SLSA](https://img.shields.io/badge/SLSA-Level%202+-0969da?logo=security)](README.md#-seguran%C3%A7a)
[![Licença: Apache 2.0](https://img.shields.io/badge/licen%C3%A7a-Apache%202.0-blue)](LICENSE)

</div>

## 📑 Sumário

- [✨ Por que usar](#-por-que-usar)
- [📦 Pacotes](#-pacotes)
- [🧬 Ecossistema TEC](#-ecossistema-tec)
- [📥 Instalação](#-instalação)
- [🚀 Início rápido](#-in%C3%ADcio-r%C3%A1pido)
- [📚 Documentação](#-documenta%C3%A7%C3%A3o)
- [⚡ Compatibilidade](#-compatibilidade)
- [🛡️ Segurança · 🧪 Testes](#️-seguran%C3%A7a--testes)
- [🤝 Contribuição · 🏷️ Versionamento · 📄 Licença](#-contribuição--versionamento--licença)

---

## ✨ Por que usar

| Sem TEC.X | Com TEC.X |
|---|---|
| Problema manual/repetitivo | Solução pronta, testada e observável |
| Coupling com infraestrutura | Abstrações limpas, trocáveis em testes |
| Observabilidade ad-hoc | `ActivitySource`/`Meter` nativos (BCL) |

- **Resiliente**: timeouts, retries, circuit breaker configuráveis
- **Seguro**: sem segredos em logs, validação de entrada, comparação em tempo constante
- **Observável**: traces, métricas e logs estruturados prontos para OpenTelemetry

---

## 📦 Pacotes

| Pacote | Para que serve | Quando instalar | Depende de |
|---|---|---|---|
| `TEC.X` | Núcleo: abstrações e implementação principal | Sempre | `TEC.Core` |
| `TEC.X.AspNetCore` | Integração ASP.NET Core (DI, middleware, filters) | Apps ASP.NET Core | `TEC.X`, `Microsoft.Extensions.DependencyInjection` |
| `TEC.X.Azure` | Integração Azure (Key Vault, Managed Identity) | Apps no Azure | `TEC.X`, `Azure.Identity` |

---

## 🧬 Ecossistema TEC

```mermaid
flowchart TB
    Core["🧰 TEC.Core<br/><sub>Result, erros, utilitários</sub>"]
    Vault["🔐 TEC.Vault<br/><sub>segredos, chaves, certificados</sub>"]
    Cqrs["🧭 TEC.Cqrs<br/><sub>commands, queries, pipeline</sub>"]
    Sec["🛡️ TEC.Security<br/><sub>autenticação, autorização</sub>"]
    Obs["📡 TEC.Observability<br/><sub>traces, métricas, logs</sub>"]
    Orm["🗄️ TEC.ORM<br/><sub>persistência</sub>"]
    Msg["📮 TEC.Messaging<br/><sub>outbox, inbox, RabbitMQ</sub>"]
    X["🎯 TEC.X<br/><sub>este componente</sub>"]
    Vault --> Core
    Cqrs --> Core
    Sec --> Core
    Sec --> Vault
    Orm --> Core
    Orm --> Cqrs
    Orm --> Vault
    Msg --> Core
    Msg --> Vault
    X --> Core
    X --> Vault
```

---

## 📥 Instalação

Feed: **GitHub Packages** (`https://nuget.pkg.github.com/tudoemcodigo/index.json`)

```bash
# PAT com escopo read:packages
dotnet nuget add source https://nuget.pkg.github.com/tudoemcodigo/index.json -n github -u SEU_USUARIO -p SEU_PAT

dotnet add package TEC.X
# ou
dotnet add package TEC.X.AspNetCore
# ou
dotnet add package TEC.X.Azure
```

---

## 🚀 Início rápido

```csharp
// Exemplo mínimo funcionando
using TEC.X;

var service = new XService();
var result = await service.DoSomethingAsync("input");
```

---

## 📚 Documentação

| Arquivo | O que responde |
|---|---|
| [📐 Uso](docs/uso.md) | Exemplos completos de API |
| [⚙️ Opções](docs/opcoes.md) | Tabela: opção, padrão, descrição |
| [❌ Erros](docs/erros.md) | Código/exceção, quando ocorre, o que fazer |
| [🛡️ Segurança](docs/seguranca.md) | Armadilhas e boas práticas |
| [⚡ Compatibilidade](docs/compatibilidade.md) | .NET 8/10, AOT, sem ICU, sistemas |

---

## ⚡ Compatibilidade

- **Frameworks**: `net8.0`, `net10.0` (LTS)
- **Native AOT**: Compatível (exceto onde documentado)
- **Globalization**: Modo *invariant* suportado (sem ICU)
- **Sistemas**: Linux, Windows, macOS (x64, arm64)

---

## 🛡️ Segurança · 🧪 Testes

- **SAST**: CodeQL `security-extended` em todo PR e push na `main`
- **Supply chain**: `NuGetAudit`, `packageSourceMapping`, lock file, actions fixadas por SHA
- **Testes**: TUnit, categorias `Integracao`, `Carga-CI`, `Carga-Pesada`, `Seguranca-Pesada`

---

## 🤝 Contribuição · 🏷️ Versionamento · 📄 Licença

- **Contribuição**: PRs bem-vindos; rode `scripts/validate-conventions.sh` antes de commitar
- **Versionamento**: [SemVer 2.0](https://semver.org/lang/pt-BR/) — prévias `preview.N` no CI, releases manuais via `release.yml` (exige aprovação no environment `publicacao`)
- **Licença**: [Apache 2.0](LICENSE) — consulte `NOTICE` para informações de atribuição do projeto

---

*Template mantido em [tudoemcodigo/tec-workflows](https://github.com/tudoemcodigo/tec-workflows).*
