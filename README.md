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

Atalhos no dashboard: `i` importa um projeto existente (informe o path da raiz), `enter` abre o projeto selecionado, `d` remove da lista de projetos conhecidos (não apaga nada em disco).

## Rodando os testes

```bash
uv run pytest
```

## Estado atual (Fase 1 — Fundação)

- Modelo de domínio agnóstico de build tool (`src/manager/models.py`).
- `MavenAdapter` com inferência completa de estrutura a partir de `pom.xml` (`src/manager/adapters/maven/`).
- Scaffold Textual navegável em modo leitura: dashboard de projetos, importação/inferência, visualização de módulos/dependências/estrutura de diretórios.
- Mutações de módulo (`add_module`/`remove_module`/`update_dependency`/`update_metadata`) ainda não implementadas — ficam para a Fase 2.

Detalhes do escopo e checklist da fase atual em `specs/phases/phase-1-fundacao/`.
