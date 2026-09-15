# Java Project Manager (jpm)

Aplicação TUI para gerenciar projetos Java (criação, metadados, módulos, estrutura de diretórios) de forma independente da build tool utilizada. Hoje suporta Maven; a arquitetura (modelo de domínio + adapters) foi feita para acomodar outras build tools no futuro.

Veja `specs/00-overview.md` para o contexto completo do produto, o glossário e o log de decisões arquiteturais. O desenvolvimento segue um fluxo de Spec-Driven Development leve, documentado em `specs/`.

## Setup

Requer Python 3.13+ e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Rodando a aplicação

```bash
uv run jpm
```

Ou, em modo de desenvolvimento (com console de debug do Textual):

```bash
uv run textual run --dev src/manager/app.py
```

A tela principal ("mvnforge", ver `specs/design/tui-layout.md`) mostra 5 painéis numerados simultaneamente: `1` Projetos, `2` Metadados, `3` Módulos, `4` BOM+Dependências, `5` Estrutura. Atalhos principais: `1`-`5`/`tab` navega entre painéis, `j`/`k` move dentro de uma lista, `n` cria (projeto/módulo), `d` remove, `enter` seleciona/edita, `space` alterna o módulo ativo em Estrutura, `:` abre o modo comando (ex.: `:modulo <nome>`).

## Rodando os testes

```bash
uv run pytest
```

## Estado atual

- **Fase 1 — Fundação**: modelo de domínio agnóstico de build tool (`src/manager/models.py`) e `MavenAdapter` com inferência completa de estrutura a partir de `pom.xml` (`src/manager/adapters/maven/`).
- **Fase 2 — Mutações** (em andamento): `add_module`, `remove_module` (com detecção de módulos dependentes) e `update_metadata` (herança de groupId/version, artifactId somente-leitura) implementados de ponta a ponta; `update_dependency` ainda é stub.
- **Fase 3 — TUI**: layout de painel único com 3 colunas/5 painéis (`src/manager/screens/main_screen.py` + `src/manager/screens/widgets/`), substituindo o fluxo de telas separadas das fases anteriores.

Detalhes de escopo e checklist de cada fase em `specs/phases/`.
