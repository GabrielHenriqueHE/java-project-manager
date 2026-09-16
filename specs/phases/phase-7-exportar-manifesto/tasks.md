# Fase 7 — Exportar Projeto para Manifesto — Tasks

- [x] **T1** — `src/manager/manifest.py`: `to_manifest`, `dump_manifest`.
- [x] **T2** — Testes de `to_manifest`/`dump_manifest`/round-trip de schema em `tests/test_manifest.py` (4 casos novos).
- [x] **T3** — Teste de round-trip completo (`tests/test_manifest_roundtrip.py`): infer → to_manifest → dump_manifest → load_manifest → create_project → infer, comparando módulos/deps/dirs com o original (fixture multi-módulo com BOM).
- [x] **T4** — `ExportManifestScreen` (`src/manager/screens/export_manifest.py`).
- [x] **T5** — Wiring: `ProjectsPanel` binding `e` → `action_export_project`; `MainScreen.export_project` novo.
- [x] **T6** — Testes de TUI em `tests/test_main_screen.py` (2 casos novos: exportar grava o YAML esperado; sem projeto selecionado não abre o form).
- [x] **T7** — Atualizar `specs/features/01-gerenciamento-de-projetos/tasks.md` e `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 147 passed (140 pré-existentes + 7 novos), nenhuma regressão; exportar um projeto multi-módulo com BOM e recriá-lo via `create_project` produz uma árvore estruturalmente equivalente à original, validado pelo teste de round-trip completo; nenhuma escrita em arquivo de build durante a exportação.
