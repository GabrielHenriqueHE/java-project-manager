# Fase 17 — Gradle: Metadados — Tasks

- [x] **T1** — `manager/adapters/common/lookup.py`: `find_parent`/`find_bom_module`/`find_dependents`/`find_managed_dependency_owner` extraídos de `MavenAdapter`; métodos privados equivalentes viram wrappers finos.
- [x] **T2** — `gradle/parser.py`: promoção de `find_block`/`CONFIG_NAMES`/`CONFIG_TO_SCOPE`/`split_coordinate`/`DEP_LINE_RE`/`PLUGIN_ID_RE`/`ROOT_NAME_RE`/`INCLUDE_RE`/`QUOTED_RE` para nomes públicos (sem mudança de comportamento).
- [x] **T3** — `gradle/writer.py` (novo): `GradleWriter.dialect`/`quote`/`plugin_id_literal`/`set_scalar`/`set_packaging`/`update_metadata`.
- [x] **T4** — `GradleAdapter.__init__(writer=None)` (mesmo padrão do `MavenAdapter`); `update_metadata` implementado.
- [x] **T5** — `tests/test_gradle_adapter_update_metadata.py` (13 casos).
- [x] **T6** — `tests/test_gradle_adapter_stubs.py`: removido o caso de `update_metadata`.
- [x] **T7** — Atualizar `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 269 passed (257 pré-existentes + 13 novos - 1 stub removido), sem regressão no `MavenAdapter`.
