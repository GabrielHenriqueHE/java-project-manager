# Fase 12 — Dependência Direta na TUI — Tasks

- [x] **T1** — `DependencyFormScreen` ganha `title`/`managed: bool = True`; `version` só obrigatória quando `managed=True`; rótulos de `type`/`scope` variam conforme `managed`.
- [x] **T2** — `MainScreen`: `_open_dependency_form` (helper compartilhado); `add_dependency` (BOM, `n`) reescrito em cima dele; novo `add_direct_dependency` (direta, `m`).
- [x] **T3** — `BomPanel`: `compose_body` ganha `#direct-deps-header`/`#direct-deps-list`; `refresh_bom(project, selected_module=None)`; `_render_direct_dependencies`; novo binding `m` → `action_add_direct_dependency`.
- [x] **T4** — Wiring de propagação: `MainScreen._refresh_all_panels` e `MainScreen.select_module` passam a chamar `BomPanel.refresh_bom` com `selected_module`.
- [x] **T5** — Testes de TUI (`tests/test_main_screen.py`, 2 casos novos): adicionar dependência direta a um módulo `packaging=jar` via Painel [4] (`m`) grava em `<dependencies>`, não em `<dependencyManagement>`/`managed_dependencies`, e aparece na seção de diretas do painel; a seção de diretas acompanha a troca de seleção no Painel [3].
- [x] **T6** — Atualizar `specs/features/03-gerenciamento-de-modulos/tasks.md` e `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 176 passed (174 pré-existentes + 2 novos), sem regressão; nenhuma mudança no backend (`MavenAdapter.update_dependency` já suportava `managed=False` desde a Fase 2) — só na TUI. O fluxo existente de dependência gerenciada (`n`) continua idêntico.
