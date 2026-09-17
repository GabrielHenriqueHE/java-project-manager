# Fase 20 — Gradle: Remover Dependência Direta — Tasks

- [x] **T1** — `GradleWriter.remove_dependency` (direta, colapso de `dependencies{}` quando fica vazio).
- [x] **T2** — `GradleAdapter.remove_direct_dependency` implementado.
- [x] **T3** — `tests/test_gradle_adapter_remove_direct_dependency.py` (9 casos).
- [x] **T4** — `tests/test_gradle_adapter_stubs.py`: removido o caso de `remove_direct_dependency`.
- [x] **T5** — Atualizar `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 295 passed, sem regressão.
