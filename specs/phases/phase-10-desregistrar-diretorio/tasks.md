# Fase 10 — Desregistrar Diretório do Build — Tasks

- [x] **T1** — `MavenPomWriter.unregister_directory_role` (`writer.py`): remove a `<execution>` pelo id recalculado, limpando `<executions>`/`<plugin>`/`<plugins>`/`<build>` em cascata.
- [x] **T2** — `BuildToolAdapter.unregister_directory_role` na interface (`base.py`).
- [x] **T3** — `MavenAdapter.unregister_directory_role` (`adapter.py`): valida módulo/role, chama o writer, levanta `ValueError` se não estava registrado.
- [x] **T4** — Testes de adapter isolados (`tests/test_maven_adapter_unregister_directory_role.py`, 8 casos) usando cópia da fixture em `tmp_path`.
- [x] **T5** — `BuildSourceFormScreen` ganha `title`/`confirm_label` opcionais (reaproveitado por registrar e desregistrar).
- [x] **T6** — Wiring: `StructurePanel` binding `u` → `MainScreen.unregister_build_source`.
- [x] **T7** — Testes de TUI (`tests/test_main_screen.py`, 2 casos): fluxo completo registrar→desregistrar remove a entrada do pom; erro quando não estava registrado não derruba a tela.
- [x] **T8** — Atualizar `specs/features/04-estrutura-de-diretorios/tasks.md`, `specs/00-overview.md` e `README.md`.

## Definição de pronto

`uv run pytest`: 168 passed (158 pré-existentes + 10 novos), sem regressão; desregistrar um diretório remove a entrada do `pom.xml` sem apagar o diretório do disco; nenhuma fixture versionada mutada pelos testes.
