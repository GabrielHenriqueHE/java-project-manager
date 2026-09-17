# Fase 19 — Gradle: Remover Dependência Gerenciada — Tasks

- [x] **T1** — `GradleWriter._remove_dep_line`/`_remove_span_and_collapse_blank_lines`/`remove_managed_dependency` (colapso em cascata de `constraints{}`/`dependencies{}`).
- [x] **T2** — `GradleAdapter.remove_dependency` implementado (usa `find_managed_dependency_owner`).
- [x] **T3** — `tests/test_gradle_adapter_remove_dependency.py` (7 casos).
- [x] **T4** — `tests/test_gradle_adapter_stubs.py`: removido o caso de `remove_dependency`.
- [x] **T5** — Atualizar `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 287 passed, sem regressão.
