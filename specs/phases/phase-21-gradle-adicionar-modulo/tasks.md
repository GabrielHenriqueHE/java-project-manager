# Fase 21 — Gradle: Adicionar Módulo — Tasks

- [x] **T1** — `GradleWriter.create_build_file` (monta `build.gradle(.kts)` do zero, reaproveitando `_render_plugins_block`/`_render_dep_line`).
- [x] **T2** — `GradleWriter.add_include` (anexa ou cria a declaração `include(...)`).
- [x] **T3** — `GradleAdapter.add_module` implementado (guards antes de qualquer escrita; `parent_name` só aceita raiz; dialeto acompanha o `settings.gradle(.kts)` existente).
- [x] **T4** — `tests/test_gradle_adapter_add_module.py` (12 casos).
- [x] **T5** — `tests/test_gradle_adapter_stubs.py`: removido o caso de `add_module`.
- [x] **T6** — Atualizar `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 306 passed, sem regressão.
