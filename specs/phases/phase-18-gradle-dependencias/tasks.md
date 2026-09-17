# Fase 18 — Gradle: Dependências — Tasks

- [x] **T1** — `GradleWriter._replace_block_content` (decomposição recursiva de blocos aninhados, sem aritmética de offset absoluto).
- [x] **T2** — `GradleWriter._render_dep_line`/`_upsert_dep_line_in_text`/`_upsert_direct_line`/`_upsert_managed_line`/`upsert_dependency`.
- [x] **T3** — `GradleAdapter.update_dependency` implementado (mesmas validações do Maven + guard de build file da Fase 17).
- [x] **T4** — `tests/test_gradle_adapter_update_dependency.py` (13 casos).
- [x] **T5** — `tests/test_gradle_adapter_stubs.py`: removido o caso de `update_dependency`.
- [x] **T6** — Atualizar `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 281 passed, sem regressão.
