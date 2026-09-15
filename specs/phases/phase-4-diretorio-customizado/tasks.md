# Fase 4 — Diretório Customizado — Tasks

- [x] **T1** — `DirectoryFormScreen` (`src/manager/screens/widgets/directory_form.py`).
- [x] **T2** — Wiring: `StructurePanel` binding `n` → `action_add_custom_directory`; `MainScreen.add_custom_directory` novo (reaproveita `MainScreen.add_directory` já existente).
- [x] **T3** — Testes de TUI em `tests/test_main_screen.py` (3 casos novos): criar diretório customizado via formulário atualiza árvore, campo vazio não confirma, cancelar não altera nada.
- [x] **T4** — Atualizar `specs/features/04-estrutura-de-diretorios/tasks.md` e `specs/00-overview.md` para refletir a segunda fatia da Fase 4.

## Definição de pronto

`uv run pytest` verde; criar diretório customizado funcional via TUI (campo de caminho livre), sem nenhuma mudança em `src/manager/adapters/`.
