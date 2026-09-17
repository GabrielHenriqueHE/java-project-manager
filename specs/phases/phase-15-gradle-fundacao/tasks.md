# Fase 15 — Gradle: Fundação (Leitura) — Tasks

- [x] **T1** — Refatoração: `manager.adapters.common.directory` (extraído de `maven/directory.py`, mesmo comportamento); `maven/directory.py` reexporta + mantém `merge_registered_directories` (exclusivo do build-helper-maven-plugin).
- [x] **T2** — `manager/adapters/gradle/parser.py`: `parse_build_file`/`parse_settings_file`, extração por regex + contagem de chaves (`_find_block`), Groovy e Kotlin DSL cobertos pelo mesmo conjunto de regexes.
- [x] **T3** — `manager/adapters/gradle/directory.py`: reexporta de `common/directory.py`.
- [x] **T4** — `manager/adapters/gradle/adapter.py`: `GradleAdapter.detect`/`infer_structure` (árvore de módulos achatada sob a raiz, packaging derivado de plugins, módulo raiz sem build file cai para `settings.gradle(.kts)`); todos os 11 métodos de mutação como stubs `NotImplementedError`.
- [x] **T5** — Registro em `services/adapters_registry.py` (`_ADAPTERS = [MavenAdapter(), GradleAdapter()]`).
- [x] **T6** — Fixtures `tests/fixtures/gradle-multi-module-groovy/` e `tests/fixtures/gradle-multi-module-kotlin/` (bom/core/api, espelhando `maven-multi-module`).
- [x] **T7** — Testes: `test_gradle_parser.py` (14 casos), `test_gradle_adapter_infer.py` (19 casos), `test_adapters_registry.py` (4 casos), `test_gradle_adapter_stubs.py` (11 casos), + 1 teste de TUI em `test_main_screen.py` (import de projeto Gradle popula todos os painéis).
- [x] **T8** — Atualizar `specs/00-overview.md` e `README.md`.

## Definição de pronto

`uv run pytest`: 241 passed (192 pré-existentes + 49 novos), sem regressão; `MavenAdapter` inalterado em comportamento (só a origem de `detect_directory_structure` mudou de arquivo); `detect_adapter` reconhece Maven, Gradle Groovy e Gradle Kotlin corretamente; um projeto Gradle multi-módulo real é navegável na TUI existente sem nenhuma mudança de painel.
