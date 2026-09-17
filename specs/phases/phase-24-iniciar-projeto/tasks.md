# Fase 24 — Iniciar Projeto do Zero — Tasks

- [x] **T1** — `src/manager/screens/init_project.py`: `InitProjectScreen`, monta `ModuleManifest` em memória a partir do formulário (build tool, groupId, artifactId, version, destino) e chama `MavenAdapter.create_project`/`GradleAdapter.create_project`.
- [x] **T2** — Wiring: binding `i` ("iniciar") em `ProjectsPanel` + `action_init_project`; `MainScreen.init_project()` reaproveitando `_on_project_registered`.
- [x] **T3** — Testes em `tests/test_main_screen.py` (7 casos): criação Maven, criação Gradle, artifactId ausente, Maven sem groupId/version, destino já existente e não-vazio, build tool inválida, cancelamento.
- [x] **T4** — Atualizar `specs/00-overview.md` (novo bullet "Fase 24") e `specs/features/01-gerenciamento-de-projetos/{requirements,tasks}.md`.

## Definição de pronto

`uv run pytest` verde (todos os pré-existentes + os 7 novos casos de `InitProjectScreen`), sem regressão em `CreateProjectScreen`/`ImportProjectScreen`/`CloneProjectScreen`; iniciar um projeto Maven de módulo único e um projeto Gradle de módulo único pelo novo formulário (binding `i`, Painel [1]) funciona de ponta a ponta — aparece na lista de projetos e fica selecionado após a criação; nenhum arquivo é escrito em disco quando artifactId/destino/build-tool estão ausentes ou inválidos, quando Maven exige groupId/version e eles faltam, ou quando o destino já existe e não está vazio; `CreateProjectScreen` permanece inalterado (hardcode de Maven é um gap conhecido, não corrigido nesta fase).
