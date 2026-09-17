# Fase 22 — Gradle: Remover Módulo — Tasks

- [x] **T1** — `GradleWriter.remove_include` (inverso de `add_include`, varre todas as declarações `include(...)`).
- [x] **T2** — `GradleAdapter.remove_module` implementado (mesma estrutura do Maven, reaproveitando `common/lookup` + `remove_managed_dependency`/`remove_dependency`).
- [x] **T3** — Correção de bug: `_FULL_DEP_LINE_RE` não vaza mais entre linhas (`\s*` → `[ \t]*` na cauda).
- [x] **T4** — `tests/test_gradle_adapter_remove_module.py` (10 casos, incluindo o cenário que expôs o bug do regex).
- [x] **T5** — `tests/test_gradle_adapter_stubs.py`: removido o caso de `remove_module` (só sobram os dois casos de `register_directory_role`/`unregister_directory_role`, permanentemente fora de escopo).
- [x] **T6** — Atualizar `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 315 passed, sem regressão.
