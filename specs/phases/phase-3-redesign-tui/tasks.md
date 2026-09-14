# Fase 3 — Reformulação da TUI — Tasks

- [ ] **T1** — `Panel` (widget base reutilizável com header `[n] TITULO` + texto dinâmico à direita).
- [ ] **T2** — `AppHeader` (cabeçalho customizado com coordenada Maven + contadores).
- [ ] **T3** — `ProjectsPanel` (Painel 1): lista, marcadores, `n`/`d`/`j`/`k`, integração com `ImportProjectScreen`/`ProjectRegistry`.
- [ ] **T4** — `ModulesPanel` (Painel 3): lista com conectores `├─`/`└─`, `n`/`d`/`j`/`k`/`enter`, integração com `ModuleFormScreen`/`ConfirmModal`/`remove_module`/`add_module`.
- [ ] **T5** — `MetadataPanel` (Painel 2): tabela chave-valor reagindo à seleção do Painel 3.
- [ ] **T6** — `BomPanel` (Painel 4): lista de `managed_dependencies`, header com nome do módulo BOM.
- [ ] **T7** — `StructurePanel` (Painel 5): checklist de 8 diretórios + árvore textual do projeto; toggle `space` do módulo ativo.
- [ ] **T8** — `CommandBar` + wiring do modo comando (`:`/`esc`/`enter`, comando `modulo <nome>`).
- [ ] **T9** — `MainScreen`: composição das 3 colunas, estado compartilhado (`project`, `selected_module`, `structure_active_module`), propagação de refresh após mutações, badge "PAINEL N".
- [ ] **T10** — Atualizar `ManagerApp` para abrir `MainScreen`; remover `screens/dashboard.py`, `screens/project_detail.py`, `screens/widgets/project_tree.py` e seus testes (`test_app_dashboard.py`, `test_project_detail_remove_module.py`, `test_project_detail_add_module.py`).
- [ ] **T11** — `tests/test_main_screen.py` cobrindo os fluxos descritos em `design.md`.
- [ ] **T12** — Ajustar `README.md` se necessário (nenhuma mudança de comando de execução esperada, só possivelmente a descrição do estado atual).

## Definição de pronto

`uv run pytest` verde; `uv run jpm` abre a nova tela com os 5 painéis, cabeçalho e rodapé conforme `specs/design/tui-layout.md`; nenhum resquício de `DashboardScreen`/`ProjectDetailScreen` no código ou nos testes.
