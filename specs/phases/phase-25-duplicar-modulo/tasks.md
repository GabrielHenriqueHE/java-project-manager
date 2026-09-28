# Fase 25 — Duplicar Módulo — Tasks

- [x] **T1** — `MavenPomWriter.set_artifact_id` + `set_parent`, com testes unitários dedicados (`tests/test_maven_pom_writer_set_artifact_id.py`, `tests/test_maven_pom_writer_set_parent.py`).
- [x] **T2** — `adapters/common/copy.py::copy_module_tree`, com teste unitário (`tests/test_adapters_common_copy.py`).
- [x] **T3** — `BuildToolAdapter.duplicate_module` — assinatura abstrata + docstring (`adapters/base.py`).
- [x] **T4** — `MavenAdapter.duplicate_module` — guards, default de `parent_name` (irmão do fonte), reparenting condicional, override opcional de `group_id`/`version` via `update_metadata`.
- [x] **T5** — `GradleAdapter.duplicate_module` — guards, cópia, `add_include`, mesmo override.
- [x] **T6** — `tests/test_maven_adapter_duplicate_module.py` (16 casos).
- [x] **T7** — `tests/test_gradle_adapter_duplicate_module.py` (13 casos, parametrizado Groovy/Kotlin).
- [x] **T8** — `DuplicateModuleFormScreen` + `MainScreen.duplicate_module` + binding `c` em `ModulesPanel`.
- [x] **T9** — Atualizar `specs/00-overview.md`, `specs/features/03-gerenciamento-de-modulos/tasks.md`, `specs/features/06-suporte-gradle/tasks.md`.

## Definição de pronto

`uv run pytest`: 367 passed, sem regressão.
