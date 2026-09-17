# Fase 14 — Remover Dependência Direta na TUI — Tasks

- [x] **T1** — `BuildToolAdapter.remove_direct_dependency` na interface (`base.py`).
- [x] **T2** — `MavenAdapter.remove_direct_dependency` (`adapter.py`): valida módulo, chama `MavenPomWriter.remove_dependency` já existente, levanta `ValueError` se não encontrada.
- [x] **T3** — Testes de adapter isolados (`tests/test_maven_adapter_remove_direct_dependency.py`, 7 casos) usando cópia da fixture em `tmp_path` — cobrindo remoção bem-sucedida, coordenadas desconhecidas, coordenadas que só existem como gerenciada (não deve remover), módulo desconhecido, fixture intocada.
- [x] **T4** — `RemoveDependencyFormScreen` (`screens/widgets/remove_dependency_form.py`): formulário dedicado, só `groupId`/`artifactId`.
- [x] **T5** — `BomPanel`: novo binding `r` → `action_remove_direct_dependency`.
- [x] **T6** — `MainScreen.remove_direct_dependency`: mesma resolução de módulo-alvo de `add_direct_dependency`; sem `ConfirmModal` (remoção pontual, sem efeito em cascata a confirmar).
- [x] **T7** — Testes de TUI (`tests/test_main_screen.py`, 2 casos): remoção bem-sucedida via Painel [4] (`r`) não afeta a entrada gerenciada equivalente no BOM; coordenadas não encontradas mostram erro sem alterar o projeto.
- [x] **T8** — Atualizar `specs/features/03-gerenciamento-de-modulos/tasks.md`, `specs/00-overview.md` e `README.md`.

## Definição de pronto

`uv run pytest`: 192 passed (183 pré-existentes + 7 de adapter + 2 de TUI), sem regressão; remover uma dependência direta de qualquer módulo via Painel [4] (`r`), sem afetar dependências gerenciadas (BOM) de mesma coordenada nem dependências diretas de outros módulos.
