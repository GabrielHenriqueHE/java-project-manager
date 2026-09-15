# Fase 4 — Estrutura de Diretórios — Tasks

- [x] **T1** — `BuildToolAdapter.add_directory` (novo método abstrato em `src/manager/adapters/base.py`).
- [x] **T2** — `MavenAdapter.add_directory` (validação de módulo/path traversal/duplicidade, `mkdir(parents=True)`, re-inferência).
- [x] **T3** — Testes de `add_directory` isolados (`tests/test_maven_adapter_add_directory.py`, 7 casos) usando cópia da fixture em `tmp_path` — cobrindo: cria diretório ausente (inclusive com pais ausentes), erro em diretório já existente, erro em módulo inexistente, erro em path traversal (`..`).
- [x] **T4** — `StructurePanel`: cursor de checklist (`_checklist_index`, `j`/`k`), destaque visual do item selecionado, `enter` → `action_create_selected`.
- [x] **T5** — Wiring: `MainScreen.add_directory` novo, distinguindo "já existe" (aviso) de outros erros (`severity="error"`).
- [x] **T6** — Testes de TUI em `tests/test_main_screen.py` (3 casos novos): criar diretório ausente via painel, navegação `j`/`k` move o item criado, repetir num item já existente não altera o estado.
- [x] **T7** — Atualizar `specs/features/04-estrutura-de-diretorios/tasks.md` (novo arquivo — a feature não tinha `tasks.md` ainda) e `specs/00-overview.md` para refletir a Fase 4.

## Definição de pronto

`uv run pytest` verde; criar um diretório do checklist funcional via API do adapter e via TUI, incluindo o caso "já existe"; nenhuma fixture versionada foi mutada pelos testes.
