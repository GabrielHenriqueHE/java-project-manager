# Fase 5 — Remover Dependência — Tasks

- [x] **T1** — `BuildToolAdapter.remove_dependency` (novo método abstrato em `src/manager/adapters/base.py`).
- [x] **T2** — `MavenAdapter.remove_dependency` (`_find_managed_dependency_owner` novo, reaproveita `MavenPomWriter.remove_managed_dependency` já existente, re-inferência).
- [x] **T3** — Testes de `remove_dependency` isolados (`tests/test_maven_adapter_remove_dependency.py`, 6 casos) usando cópia da fixture em `tmp_path` — cobrindo: remove entrada gerenciada existente, resultado bate com re-inferência, remover a última entrada limpa `<dependencyManagement>`, erro em dependência inexistente, remoção não mexe em dependência direta com mesma coordenada.
- [x] **T4** — `BomPanel`: guarda `self._dependencies`, novo `dependency_at`, binding `d` → `action_remove_dependency`. Corrigido bug pré-existente: `refresh_bom` não setava `list_view.index` após popular a lista.
- [x] **T5** — Wiring: `MainScreen.remove_dependency` novo.
- [x] **T6** — Testes de TUI em `tests/test_main_screen.py` (2 casos novos): remover entrada via painel atualiza a lista/Painel [4], remover a última entrada volta ao estado vazio.
- [x] **T7** — Atualizar `specs/features/03-gerenciamento-de-modulos/tasks.md` e `specs/00-overview.md` para refletir a Fase 5.

## Definição de pronto

`uv run pytest` verde; remover uma dependência gerenciada funcional via API do adapter e via TUI; nenhuma fixture versionada foi mutada pelos testes.
