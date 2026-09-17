# Fase 13 — Clonar Repositório Remoto — Tasks

- [x] **T1** — `src/manager/services/git.py`: `GitCloneError`, `clone_repository` (shell-out a `git clone` via `subprocess`; valida git instalado e destino vazio antes de clonar).
- [x] **T2** — Testes isolados (`tests/test_git_service.py`, 5 casos) contra um repositório git real criado em `tmp_path`, clonado por path local (sem rede): clone bem-sucedido, origem inexistente, destino não-vazio, destino vazio existente permitido, git ausente (mock de `shutil.which`).
- [x] **T3** — `CloneProjectScreen` (`screens/clone_project.py`): formulário com dois campos (URL, destino); reaproveita `detect_adapter`/`infer_structure`/`ProjectRegistry.add` após o clone, mesmo padrão de `ImportProjectScreen`.
- [x] **T4** — `ProjectsPanel`: novo binding `g` → `action_clone_project`.
- [x] **T5** — `MainScreen`: `_on_project_registered` extraído do closure de `import_project` e reaproveitado por `import_project`/`clone_project`.
- [x] **T6** — Testes de TUI (`tests/test_main_screen.py`, 2 casos): clone de um repositório local (via `git init`+commit em `project_root`) popula todos os painéis igual a um import; destino não-vazio mostra erro e não altera nada.
- [x] **T7** — Atualizar `specs/features/01-gerenciamento-de-projetos/tasks.md`, `specs/00-overview.md` e `README.md` (incluindo nota de que `git` é um requisito de sistema só para esta operação).

## Definição de pronto

`uv run pytest`: 183 passed (176 pré-existentes + 7 novos), sem regressão; clonar um repositório remoto (testado com path local, sem depender de rede) e ter o projeto resultante registrado e navegável na TUI, com o mesmo resultado final de importar um path já existente.
