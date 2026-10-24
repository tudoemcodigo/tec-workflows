# Instruções para agentes — tec-workflows

Este arquivo complementa as instruções herdadas de `D:\Projetos\Componentes\AGENTS.md` com o contexto deste repositório. Em caso de conflito, prevalecem as instruções do usuário e as regras herdadas.

## Propósito e limites

`tec-workflows` fornece CI/CD reutilizável, composite actions e arquivos canônicos de build para os componentes `lib-tec-*`. Não é uma biblioteca de runtime. Trate workflows, actions e templates como contratos consumidos por outros repositórios.

O escopo padrão é este repositório. Não altere repositórios `TEC.*` vizinhos, não publique tags/releases e não execute sincronizações que escrevam nos componentes sem pedido explícito do usuário.

## Mapa do repositório

- `.github/workflows/`: workflows reutilizáveis de CI, release, testes, CodeQL, benchmark e lint.
- `actions/`: composite actions e scripts chamados por workflows. `actions/release-gates/` contém os portões de PR e `ci-ok` do release.
- `template/`: fonte canônica dos arquivos compartilhados com os componentes. Edite o template aqui; não edite cópias dentro de componentes.
- `scripts/sync-template.sh`: copia o template para repositórios vizinhos e modifica esses diretórios. Confira os destinos antes de executá-lo; sem argumentos, ele tenta sincronizar todos os componentes vizinhos.
- `scripts/validate-conventions.sh`: valida localmente arquivos canônicos e convenções do projeto consumidor.
- `tests/`: testes Python dos scripts e das regras auxiliares.
- `README.md`: guia principal de consumo, parâmetros, permissões, publicação e template.
- `docs/padroes.md`: padrões de engenharia e resumo dos fluxos dos componentes.

## Regras para mudanças

1. Antes de editar, confira `git status` e `git diff`. Preserve alterações existentes do usuário; não use reset, checkout destrutivo ou limpeza de arquivos para “começar do zero”.
2. Workflows reutilizáveis e actions versionadas têm consumidores externos. Ao mudar entradas, saídas, permissões ou comportamento, atualize a documentação e procure todas as chamadas e exemplos no repositório.
3. Permissões concedidas a um workflow chamado não podem exceder as do chamador. O release consulta PRs e Checks API: consumidores devem conceder `pull-requests: read` e `checks: read`, além das permissões de publicação descritas no README.
4. O release usa `publish-environment` (padrão `publicacao`) nos jobs de criação da tag/Release e de publicação no feed. O valor não pode ficar vazio. Mantenha essa proteção ao alterar o fluxo.
5. Os portões de release devem falhar fechados: falha da API, ausência de `ci-ok` ou execução mais recente sem conclusão `success` bloqueiam a publicação. `allow-open-prs: true` é a única exceção explícita ao bloqueio de PRs; não remove a exigência de `ci-ok`.
6. Valide os pacotes antes de criar a tag/Release e preserve a geração do atestado de proveniência antes dessa publicação. Mantenha as etapas recuperáveis e idempotentes.
7. Não exponha tokens, secrets, credenciais ou conteúdo não confiável em logs, annotations ou Markdown de resumo. Actions externas devem permanecer fixadas por SHA conforme o padrão atual.
8. As referências `@v1` são a versão documentada nos exemplos centrais. Antes de afirmar que todos os componentes consumidores já migraram, confira o estado real deles; não os atualize como parte deste repositório sem autorização.
9. Mantenha `README.md`, `docs/padroes.md` e `CHANGELOG.md` coerentes com alterações de contrato e comportamento.

## Verificação

Execute a suíte Python e os linters disponíveis após mudanças relevantes:

```bash
python3 -m unittest discover -s tests -v
actionlint -color
shellcheck scripts/*.sh
git diff --check
```

O workflow `.github/workflows/lint.yml` é a referência para a verificação no CI: roda `actionlint`, `zizmor`, `shellcheck` e os testes Python em Ubuntu. Alguns testes em `tests/test_check_conventions.py` reproduzem etapas Bash e são ignorados no Windows; confirme-os em Ubuntu/CI.

Para validar convenções de um consumidor, use `scripts/validate-conventions.sh <caminho-do-repositório>` em Bash. Não execute `scripts/sync-template.sh` como parte de uma auditoria somente de leitura: ele copia arquivos para outros repositórios.
