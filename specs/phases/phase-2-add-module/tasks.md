# Fase 2 — Adicionar Módulo — Tasks

- [x] **T1** — `xml_utils.append_with_matching_indent` (inserção genérica preservando indentação).
- [x] **T2** — `MavenPomWriter.add_module_entry` e `MavenPomWriter.create_pom`.
- [x] **T3** — `MavenAdapter.add_module` (resolução de pai, validações, criação de diretórios/pom, registro no pai, re-inferência).
- [x] **T4** — Testes de `add_module` isolados (`tests/test_maven_adapter_add_module.py`, 10 casos) usando cópia da fixture em `tmp_path`.
- [x] **T5** — `ModuleFormScreen` (`src/manager/screens/widgets/module_form.py`).
- [x] **T6** — Wiring na `ProjectDetailScreen`: binding `a`, generalização de `_apply_updated_project` para aceitar mensagem customizada.
- [x] **T7** — Testes de TUI (`tests/test_project_detail_add_module.py`): criação sob a raiz, cancelamento, erro de pai não-pom.
- [x] **T8** — Atualizar `specs/features/03-gerenciamento-de-modulos/tasks.md` e `specs/00-overview.md` para refletir que `add_module` saiu do estado de stub.

## Definição de pronto

`uv run pytest` verde (41 testes); criação de módulo funcional via API do adapter e via TUI, incluindo herança de groupId/version e dependências iniciais; nenhuma fixture versionada foi mutada pelos testes.
