# Fase 2 — Remover Módulo — Tasks

- [x] **T1** — Extrair `xml_utils.py` (namespace + remoção preservando whitespace) e refatorar `MavenPomParser` para usá-lo.
- [x] **T2** — Implementar `MavenPomWriter` (`remove_module_entry`, `remove_managed_dependency`, `remove_dependency`) com limpeza de containers vazios e normalização da declaração XML.
- [x] **T3** — Implementar `MavenAdapter.remove_module` (busca de módulo/pai/BOM/dependentes, `DependentModuleConflict`, escrita via `MavenPomWriter`, re-inferência do resultado).
- [x] **T4** — Testes de `remove_module` isolados (`tests/test_maven_adapter_remove_module.py`, 9 casos) usando cópia da fixture em `tmp_path` — a fixture versionada nunca é mutada.
- [x] **T5** — `ConfirmModal` reutilizável (`src/manager/screens/widgets/confirm_dialog.py`).
- [x] **T6** — Wiring na `ProjectDetailScreen`: binding `r`, captura de `DependentModuleConflict`, `ProjectTree.refresh_project`.
- [x] **T7** — Testes de TUI (`tests/test_project_detail_remove_module.py`): remoção direta, conflito confirmado, conflito cancelado.
- [x] **T8** — Atualizar `specs/features/03-gerenciamento-de-modulos/tasks.md` para refletir que `remove_module` saiu do estado de stub.

## Definição de pronto

`uv run pytest` verde (29 testes); remoção de módulo funcional via API do adapter e via TUI, com e sem conflito de dependentes; nenhuma fixture versionada foi mutada pelos testes.
