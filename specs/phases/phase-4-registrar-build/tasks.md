# Fase 4 — Registrar Diretório no Build — Tasks

- [ ] **T1** — `BuildToolAdapter.register_directory_role` (novo método abstrato em `src/manager/adapters/base.py`).
- [ ] **T2** — `MavenPomWriter.register_directory_role` (`_find_plugin_element`, `_find_execution_element`, construção de `<build><plugins><plugin><executions><execution>` idempotente).
- [ ] **T3** — `MavenAdapter.register_directory_role` (validação de módulo/role/diretório existente, re-inferência).
- [ ] **T4** — Testes isolados (`tests/test_maven_adapter_register_directory_role.py`) usando cópia da fixture em `tmp_path` — cobrir: registra `source` novo (cria `<build>` do zero), registra `resource` (estrutura `<resources><resource><directory>`), segunda pasta/role reaproveita o mesmo `<plugin>`, idempotência (mesma pasta/role duas vezes não duplica), erro em diretório inexistente, erro em role inválido, erro em módulo inexistente.
- [ ] **T5** — `BuildSourceFormScreen` (`src/manager/screens/widgets/build_source_form.py`).
- [ ] **T6** — Wiring: `StructurePanel` binding `b` → `action_register_build_source`; `MainScreen.register_build_source` novo.
- [ ] **T7** — Testes de TUI em `tests/test_main_screen.py`: registrar via formulário escreve no pom, cancelar não altera nada, role inválido mantém o formulário aberto com feedback.
- [ ] **T8** — Atualizar `specs/features/04-estrutura-de-diretorios/tasks.md` e `specs/00-overview.md` para refletir a quarta fatia da Fase 4.

## Definição de pronto

`uv run pytest` verde; registrar um diretório customizado no build funcional via API do adapter e via TUI; nenhuma fixture versionada foi mutada pelos testes.
