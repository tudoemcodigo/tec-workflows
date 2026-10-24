# CHANGELOG.md

Sequência de versões do repositório `tec-workflows`.

## [1.0.0] - 2026-10-24

### Adicionado
- Primeira publicação dos workflows reutilizáveis, composite actions, arquivos canônicos de build e documentação.
- Portões de segurança para release e validação local de convenções.

### Corrigido
- **Portões de publicação**: chamadas à API do GitHub que falham ou não encontram `ci-ok` agora bloqueiam o release.
- **Relatório de testes**: corrigidos o carregamento dos testes, a extração do TFM e o escape de dados não confiáveis no resumo.
- **Aprovação do release**: o mesmo environment protege a criação da tag/Release e a publicação no feed; o atestado é gerado antes da criação da Release.


Veja as versões e notas nas [Releases do GitHub](https://github.com/tudoemcodigo/tec-workflows/releases).
