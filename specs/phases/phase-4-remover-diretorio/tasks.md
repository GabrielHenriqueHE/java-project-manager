# Fase 4 — Remover Diretório — Tasks

- [x] **T1** — `BuildToolAdapter.remove_directory` (novo método abstrato em `src/manager/adapters/base.py`).
- [x] **T2** — `MavenAdapter.remove_directory` (extrai `_resolve_module_relative_path` reaproveitado por `add_directory`; valida existência/vazio; `rmdir()`; re-inferência).
- [x] **T3** — Testes de `remove_directory` isolados (`tests/test_maven_adapter_remove_directory.py`, 8 casos) usando cópia da fixture em `tmp_path` — cobrindo: remove diretório vazio, erro em diretório não-vazio, erro em diretório inexistente, erro em módulo inexistente, erro em path traversal, erro ao tentar remover o próprio diretório do módulo.
- [x] **T4** — `StructurePanel`: binding `d` → `action_remove_selected`.
- [x] **T5** — Wiring: `MainScreen.remove_directory` novo, distinguindo "não existe" (aviso) de outros erros (`severity="error"`).
- [x] **T6** — Testes de TUI em `tests/test_main_screen.py` (3 casos novos): remover item do checklist via painel atualiza checklist/árvore, remover item não-vazio mostra erro sem alterar nada, remover item já ausente mostra aviso sem alterar nada.
- [x] **T7** — Atualizar `specs/features/04-estrutura-de-diretorios/tasks.md` e `specs/00-overview.md` para refletir a terceira fatia da Fase 4.

## Definição de pronto

`uv run pytest` verde; remover um diretório vazio do checklist funcional via API do adapter e via TUI; nenhuma fixture versionada foi mutada pelos testes.
