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

A tela principal ("mvnforge", ver `specs/design/tui-layout.md`) mostra 5 painéis numerados simultaneamente: `1` Projetos, `2` Metadados, `3` Módulos, `4` BOM+Dependências, `5` Estrutura. Atalhos principais: `1`-`5`/`tab` navega entre painéis, `j`/`k` move dentro de uma lista ou do checklist em Estrutura, `n` cria (projeto/módulo/dependência/diretório customizado), `d` remove, `enter` seleciona/edita (ou cria o diretório destacado em Estrutura), `b` registra o diretório ativo no build (Estrutura), `space` alterna o módulo ativo em Estrutura, `:` abre o modo comando (ex.: `:modulo <nome>`).

## Rodando os testes

```bash
uv run pytest
```

## Estado atual

- **Fase 1 — Fundação**: modelo de domínio agnóstico de build tool (`src/manager/models.py`) e `MavenAdapter` com inferência completa de estrutura a partir de `pom.xml` (`src/manager/adapters/maven/`).
- **Fase 2 — Mutações** (concluída): `add_module`, `remove_module` (com detecção de módulos dependentes), `update_metadata` (herança de groupId/version, artifactId somente-leitura) e `update_dependency` (upsert de dependências gerenciadas/diretas) implementados de ponta a ponta.
- **Fase 3 — TUI**: layout de painel único com 3 colunas/5 painéis (`src/manager/screens/main_screen.py` + `src/manager/screens/widgets/`), substituindo o fluxo de telas separadas das fases anteriores.
- **Fase 4 — Estrutura de Diretórios** (em andamento): `add_directory`/`remove_directory` criam/removem em disco os itens do checklist do Painel [5] ESTRUTURA (navegue com `j`/`k`, `enter` cria, `d` remove se vazio) ou um caminho customizado digitado via `n` (só criação); `register_directory_role` (`b`) registra um diretório existente como fonte/recurso extra no build via `build-helper-maven-plugin`, e `infer_structure` já lê essas entradas de volta.
- **Fase 5 — Remover Dependência** (concluída): `remove_dependency` remove uma entrada gerenciada (BOM) do Painel [4] (`d` sobre a entrada destacada).
- **Fase 6 — Criar Projeto a Partir de Manifesto** (concluída): `create_project` materializa um projeto novo em disco a partir de um manifesto YAML (`ModuleManifest`). Painel [1], binding `c`.
- **Fase 7 — Exportar Projeto para Manifesto** (concluída): operação inversa — `to_manifest`/`dump_manifest` serializam um projeto carregado para o mesmo dialeto YAML. Painel [1], binding `e`.
- **Fase 8 — Código-Fonte na Exportação** (concluída): `export_source_files` copia o conteúdo real dos arquivos (não só a estrutura) dos módulos que batem com um padrão de nome; `create_project` reproduz esse conteúdo via `source_root` opcional.
- **Fase 9 — Marcar Diretório Registrado no Build** (concluída): a árvore do Painel [5] distingue visualmente um diretório de convenção padrão de um registrado via `build-helper-maven-plugin` (sufixo `(build)`).

Detalhes de escopo e checklist de cada fase em `specs/phases/`.
