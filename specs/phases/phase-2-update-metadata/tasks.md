# Fase 2 — Atualizar Metadados — Tasks

- [x] **T1** — `xml_utils.ensure_child_in_order` (inserção genérica respeitando a ordem do XSD do POM) + `_POM_ELEMENT_ORDER`.
- [x] **T2** — `MavenPomWriter.update_metadata` (groupId/version/name/description com set-ou-remove, packaging sempre explícito, java.version via properties, limpeza de containers vazios).
- [x] **T3** — `MavenAdapter.update_metadata` (validação de artifactId somente-leitura, validação de packaging vs. submódulos/BOM, resolução de herança de groupId/version via pai, re-inferência).
- [x] **T4** — Testes de `update_metadata` isolados (`tests/test_maven_adapter_update_metadata.py`, 11 casos) usando cópia da fixture em `tmp_path` — cobrindo: edição simples de name/description, limpar campo remove tag, herança de groupId/version (raiz vs. módulo filho), erro de artifactId diferente, erro de packaging em módulo com submódulos/BOM, erro de raiz sem groupId/version, inserção de tag ausente respeitando ordem do XSD.
- [x] **T5** — `MetadataFormScreen` (`src/manager/screens/widgets/metadata_form.py`).
- [x] **T6** — Wiring: `MetadataPanel` guarda `self._module` e `action_edit` delega para `MainScreen.update_metadata`; `MainScreen.update_metadata` novo.
- [x] **T7** — Testes de TUI em `tests/test_main_screen.py` (3 casos novos): edição bem-sucedida atualiza painéis, cancelamento não altera nada, erro do adapter vira notificação.
- [x] **T8** — Atualizar `specs/features/02-metadados-do-projeto/tasks.md`, `specs/features/03-gerenciamento-de-modulos/tasks.md` e `specs/00-overview.md` para refletir que `update_metadata` saiu do estado de stub.

## Definição de pronto

`uv run pytest` verde; edição de metadados funcional via API do adapter e via TUI, incluindo herança de groupId/version e limpeza de campos; nenhuma fixture versionada foi mutada pelos testes.
