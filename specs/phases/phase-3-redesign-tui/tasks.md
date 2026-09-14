# Fase 3 — Reformulação da TUI — Tasks

- [x] **T1** — `Panel` (widget base reutilizável com header `[n] TITULO` + texto dinâmico à direita).
- [x] **T2** — `AppHeader` (cabeçalho customizado com coordenada Maven + contadores).
- [x] **T3** — `ProjectsPanel` (Painel 1): lista, marcadores, `n`/`d`/`j`/`k`, integração com `ImportProjectScreen`/`ProjectRegistry`.
- [x] **T4** — `ModulesPanel` (Painel 3): lista com conectores `├─`/`└─`, `n`/`d`/`j`/`k`/`enter`, integração com `ModuleFormScreen`/`ConfirmModal`/`remove_module`/`add_module`.
- [x] **T5** — `MetadataPanel` (Painel 2): tabela chave-valor reagindo à seleção do Painel 3.
- [x] **T6** — `BomPanel` (Painel 4): lista de `managed_dependencies`, header com nome do módulo BOM.
- [x] **T7** — `StructurePanel` (Painel 5): checklist de 8 diretórios + árvore textual do projeto; toggle `space` do módulo ativo.
- [x] **T8** — `CommandBar` + wiring do modo comando (`:`/`esc`/`enter`, comando `modulo <nome>`).
- [x] **T9** — `MainScreen`: composição das 3 colunas, estado compartilhado (`project`, `selected_module`), propagação de refresh após mutações, badge "PAINEL N".
- [x] **T10** — `ManagerApp` atualizado para abrir `MainScreen`; removidos `screens/dashboard.py`, `screens/project_detail.py`, `screens/widgets/project_tree.py` e seus testes (`test_app_dashboard.py`, `test_project_detail_remove_module.py`, `test_project_detail_add_module.py`).
- [x] **T11** — `tests/test_main_screen.py` (9 testes) cobrindo estado vazio, import, navegação, add/remove módulo, toggle de estrutura, modo comando, remoção de projeto.
- [x] **T12** — `README.md` atualizado com o novo layout e estado por fase.

## Definição de pronto

`uv run pytest` verde (40 testes); `uv run jpm` abre a nova tela com os 5 painéis, cabeçalho e rodapé conforme `specs/design/tui-layout.md`; nenhum resquício de `DashboardScreen`/`ProjectDetailScreen` no código ou nos testes. Screenshot de validação visual gerado via `App.export_screenshot()` e enviado ao usuário para revisão.

## Notas de bugs encontrados e corrigidos durante a implementação

- `Panel.focus_default()` (base) só chama `self.focus()`, o que é um no-op em painéis com `can_focus = False` (os baseados em `ListView`). `ProjectsPanel`, `ModulesPanel` e `BomPanel` precisaram sobrescrever `focus_default()` delegando ao `ListView` interno — sem isso, a navegação por `1`-`5` parecia não fazer nada.
- Um binding declarado num painel-ancestral (`Panel.BINDINGS`) não é automaticamente executado sobre o widget focado (ex.: `ListView`) — é necessário implementar `action_cursor_down`/`action_cursor_up` no próprio painel delegando explicitamente à lista interna.
- `ProjectsPanel.refresh_projects` reconstruía a lista sem restaurar `list_view.index`, então qualquer refresh (inclusive o disparado pela própria seleção) zerava a seleção e quebrava o atalho `d` logo em seguida — corrigido restaurando o índice do projeto ativo após popular a lista, no mesmo padrão já usado por `ModulesPanel`.
