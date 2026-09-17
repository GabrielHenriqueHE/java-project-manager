# Fase 11 — Remover Diretório Não-Vazio / Caminho Livre — Tasks

- [x] **T1** — `DirectoryNotEmptyConflict` (`base.py`), ao lado de `DependentModuleConflict`.
- [x] **T2** — `BuildToolAdapter.remove_directory` ganha `force: bool = False` na interface (`base.py`).
- [x] **T3** — `MavenAdapter.remove_directory`: `force=False` levanta `DirectoryNotEmptyConflict` em diretório não-vazio; `force=True` remove recursivamente (`shutil.rmtree`); guarda do diretório-raiz do módulo continua incondicional.
- [x] **T4** — Testes de adapter (`tests/test_maven_adapter_remove_directory.py`): teste existente de "não-vazio" migrado de `ValueError` para `DirectoryNotEmptyConflict`; 3 casos novos (`force` remove recursivamente, `force` ainda remove vazio, `force` não contorna a guarda do diretório-raiz).
- [x] **T5** — `DirectoryFormScreen` ganha `title`/`confirm_label` opcionais (mesmo padrão da Fase 10 em `BuildSourceFormScreen`).
- [x] **T6** — `MainScreen.remove_directory` reescrito no padrão `_do_remove(force)`/`ConfirmModal` de `remove_module`; novo `MainScreen.remove_custom_directory` (form de caminho livre, delega para `remove_directory`).
- [x] **T7** — `StructurePanel`: novo binding `x` → `action_remove_custom_directory`.
- [x] **T8** — Testes de TUI (`tests/test_main_screen.py`): teste existente de "erro em não-vazio" atualizado para o novo fluxo de confirmação; 1 caso novo de confirmação efetiva (remove recursivamente); 2 casos novos para o binding `x` (remove por caminho livre; não-vazio por caminho livre também pede confirmação).
- [x] **T9** — Atualizar `specs/features/04-estrutura-de-diretorios/tasks.md` (fecha a feature) e `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 174 passed (168 pré-existentes + 6 novos), sem regressão; remover um diretório não-vazio pede confirmação e, confirmado, remove recursivamente; remover qualquer diretório do módulo (não só os 8 itens do checklist) funciona pelo formulário de caminho livre (`x`); remover o diretório-raiz do módulo continua bloqueado mesmo com `force=True`.
