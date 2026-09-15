# Fase 2 — Atualizar Dependência — Tasks

- [ ] **T1** — Estender `_append_dependency_element` para escrever `type`/`classifier` (além de `groupId`/`artifactId`/`version`/`scope`), reordenando conforme o XSD (`groupId`, `artifactId`, `version`, `type`, `classifier`, `scope`).
- [ ] **T2** — `MavenPomWriter.update_dependency` (upsert por `(groupId, artifactId)` em `dependencies` ou `dependencyManagement/dependencies`, criando as seções via `ensure_child_in_order` quando ausentes).
- [ ] **T3** — `MavenAdapter.update_dependency` (validação de packaging=pom para entradas gerenciadas, validação de version obrigatória para gerenciadas, re-inferência).
- [ ] **T4** — Testes de `update_dependency` isolados (`tests/test_maven_adapter_update_dependency.py`) usando cópia da fixture em `tmp_path` — cobrir: criar entrada gerenciada nova (sem `dependencyManagement` prévio), atualizar entrada existente (mesma groupId:artifactId, versão diferente), erro de version ausente, erro de packaging != pom, dependência direta (managed=False) em módulo comum.
- [ ] **T5** — `DependencyFormScreen` (`src/manager/screens/widgets/dependency_form.py`).
- [ ] **T6** — Wiring: `BomPanel.action_add_dependency` delega para `MainScreen.add_dependency`; `MainScreen.add_dependency` novo.
- [ ] **T7** — Testes de TUI em `tests/test_main_screen.py`: adicionar dependência bem-sucedida atualiza Painel [4], cancelamento não altera nada, erro do adapter vira notificação.
- [ ] **T8** — Atualizar `specs/features/03-gerenciamento-de-modulos/tasks.md` e `specs/00-overview.md` para refletir que `update_dependency` saiu do estado de stub (última fatia planejada da Fase 2).

## Definição de pronto

`uv run pytest` verde; adicionar/atualizar dependência gerenciada funcional via API do adapter e via TUI; nenhuma fixture versionada foi mutada pelos testes.
