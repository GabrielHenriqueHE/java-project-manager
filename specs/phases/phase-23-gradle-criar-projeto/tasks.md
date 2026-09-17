# Fase 23 — Gradle: Criar Projeto — Tasks

- [x] **T1** — `GradleAdapter._validate_gradle_manifest` (validações do Maven menos a exigência de group/version na raiz).
- [x] **T2** — `GradleAdapter.create_project` implementado (settings.gradle + `create_build_file` por módulo, sempre Groovy).
- [x] **T3** — `GradleAdapter._materialize_directories` (cria/copia diretórios, sem registro de build).
- [x] **T4** — `tests/test_gradle_adapter_create_project.py` (13 casos).
- [x] **T5** — `tests/test_gradle_adapter_stubs.py`: removido o caso de `create_project` (só sobram `register_directory_role`/`unregister_directory_role`, permanentemente fora de escopo).
- [x] **T6** — Docstring da classe `GradleAdapter` e comentários de seção atualizados para refletir que só os dois métodos de `sourceSets{}` seguem stub.
- [x] **T7** — Atualizar `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 327 passed, sem regressão. [[06-suporte-gradle]] completa dentro do escopo definido.
