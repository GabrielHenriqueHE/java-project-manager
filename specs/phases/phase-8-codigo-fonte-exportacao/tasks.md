# Fase 8 — Código-Fonte na Exportação — Tasks

- [x] **T1** — `src/manager/manifest.py`: `export_source_files`.
- [x] **T2** — `BuildToolAdapter.create_project`: parâmetro `source_root` documentado (`src/manager/adapters/base.py`).
- [x] **T3** — `MavenAdapter.create_project`/`_materialize`/`_materialize_directories`: suporte a `source_root` (copia em vez de `mkdir` quando existir snapshot).
- [x] **T4** — Testes de `export_source_files` em `tests/test_manifest.py` (3 casos).
- [x] **T5** — Testes de `create_project(source_root=...)` em `tests/test_maven_adapter_create_project.py` (3 casos).
- [x] **T6** — Round-trip completo estendido em `tests/test_manifest_roundtrip.py` (exportar com padrão, recriar, comparar conteúdo de arquivo byte-a-byte; módulo fora do padrão fica só com diretório vazio).
- [x] **T7** — `ExportManifestScreen`: campo `#source-pattern-input`.
- [x] **T8** — `CreateProjectScreen`: detecção automática de `.files` ao lado do manifesto.
- [x] **T9** — Teste de TUI em `tests/test_main_screen.py` (fluxo completo: exportar com padrão → criar → arquivo copiado).
- [x] **T10** — Atualizar `specs/features/01-gerenciamento-de-projetos/tasks.md` e `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 155 passed (147 pré-existentes + 8 novos), sem regressão; exportar um módulo com padrão de nome preserva o conteúdo real dos arquivos numa pasta `.files` ao lado do manifesto; criar um projeto a partir desse manifesto reproduz os arquivos com conteúdo idêntico nos módulos correspondentes, mantendo diretórios vazios para os demais; `create_project` sem `source_root` continua idêntico ao comportamento anterior à fatia.
