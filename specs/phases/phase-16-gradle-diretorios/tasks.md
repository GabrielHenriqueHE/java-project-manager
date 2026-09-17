# Fase 16 — Gradle: Diretórios — Tasks

- [x] **T1** — `manager/adapters/common/lookup.py`: `find_module`/`resolve_module_relative_path` extraídos de `MavenAdapter._find_module`/`_resolve_module_relative_path`.
- [x] **T2** — `MavenAdapter._find_module`/`_resolve_module_relative_path` viram wrappers finos sobre `common.lookup` (zero mudança de comportamento, call sites existentes intocados).
- [x] **T3** — `GradleAdapter.add_directory`/`remove_directory`: implementação real (mesmo corpo do `MavenAdapter`, via `common.lookup` + `DirectoryNotEmptyConflict`).
- [x] **T4** — `tests/test_gradle_adapter_add_directory.py` (7 casos) e `tests/test_gradle_adapter_remove_directory.py` (10 casos), espelhando os testes Maven equivalentes.
- [x] **T5** — `tests/test_gradle_adapter_stubs.py`: removidos os casos de `add_directory`/`remove_directory`.
- [x] **T6** — Atualizar `specs/00-overview.md` e `specs/features/06-suporte-gradle/tasks.md`.

## Definição de pronto

`uv run pytest`: 257 passed (todos os pré-existentes + 17 novos), sem regressão no `MavenAdapter`; um projeto Gradle carregado na TUI aceita criar/remover diretórios pelo Painel [5] sem nenhuma mudança de código de apresentação.
