# Fase 4 — Inferir Diretórios Registrados no Build — Tasks

- [x] **T1** — Novo módulo `src/manager/adapters/maven/build_helper.py` com `GROUP_ID`/`ARTIFACT_ID`/`VERSION`/`ROLE_GOAL_PHASE`/`GOAL_ROLE`; `writer.py` atualizado para importar de lá (remove as constantes locais duplicadas, sem mudança de comportamento).
- [x] **T2** — `MavenPomParser`: `ParsedPom.registered_directories`, `_parse_registered_directories`/`_is_build_helper_plugin`/`_parse_execution_directories`.
- [x] **T3** — `directory.py`: `merge_registered_directories`.
- [x] **T4** — `MavenAdapter._build_module` chama `merge_registered_directories` após `detect_directory_structure`.
- [x] **T5** — Testes (`tests/test_maven_adapter_infer_build_plugins.py`, 9 casos): source registrado aparece em `source_dirs`; resource registrado aparece em `resource_dirs` (via `<resources><resource><directory>`); test-source/test-resource aparecem em `test_dirs`/`test_resource_dirs`; diretório registrado mas apagado do disco não aparece; pom sem o plugin não é afetado; plugin não relacionado (`maven-compiler-plugin`) é ignorado sem erro; registrar um dir já padrão não duplica a entrada; determinismo (duas inferências seguidas são iguais); fixture versionada intocada.
- [x] **T6** — Suíte completa (`uv run pytest`): 117 passed (108 pré-existentes + 9 novos), nenhuma regressão.
- [x] **T7** — Atualizar `specs/features/04-estrutura-de-diretorios/tasks.md` (mover "ler de volta o `<build><plugins>`" de "fora de escopo" para concluído) e `specs/00-overview.md` (fatia 5 da Fase 4).

## Definição de pronto

`uv run pytest` verde; `MavenAdapter().infer_structure(...)` reflete, em `directory_structure.source_dirs`/`test_dirs`/`resource_dirs`/`test_resource_dirs`, qualquer diretório já registrado via `build-helper-maven-plugin` que ainda exista em disco; nenhuma fixture versionada mutada pelos testes; nenhuma escrita em disco nesta fatia.
