# Fase 6 — Criar Projeto a Partir de Manifesto — Tasks

- [x] **T1** — `pyproject.toml`: adiciona `pyyaml` às dependências de produção.
- [x] **T2** — `src/manager/manifest.py`: `ModuleManifest`, `load_manifest`, `is_bom_manifest`, `validate_manifest_tree`.
- [x] **T3** — `directory.py`: rename `_STANDARD_DIRS` → `STANDARD_DIRS` (público).
- [x] **T4** — `MavenPomWriter.create_pom`: `parent_*` opcionais (omite `<parent>` se ausentes) + novo `submodule_names` (escreve `<modules>`).
- [x] **T5** — `BuildToolAdapter.create_project` (novo método abstrato em `src/manager/adapters/base.py`).
- [x] **T6** — `MavenAdapter.create_project` + `_validate_maven_manifest` + `_materialize` + `_materialize_directories`.
- [x] **T7** — Testes de `manifest.py` (`tests/test_manifest.py`, 4 casos).
- [x] **T8** — Testes de `create_pom` parent-opcional/`submodule_names` (`tests/test_maven_pom_writer_create_pom.py`, 4 casos).
- [x] **T9** — Testes de `MavenAdapter.create_project` (`tests/test_maven_adapter_create_project.py`, 12 casos: módulo único, herança multi-módulo, BOM, diretório convencional vs. customizado, e 6 casos de validação/erro sem escrita em disco).
- [x] **T10** — `CreateProjectScreen` (`src/manager/screens/create_project.py`).
- [x] **T11** — Wiring: `ProjectsPanel` binding `c` → `action_create_project`; `MainScreen.create_project` novo.
- [x] **T12** — Testes de TUI em `tests/test_main_screen.py` (3 casos novos: fluxo completo via formulário, manifesto inválido mantém o form aberto, cancelar não cria nada).
- [x] **T13** — Atualizar `specs/features/01-gerenciamento-de-projetos/tasks.md` e `specs/00-overview.md`.

## Definição de pronto

`uv run pytest`: 140 passed (117 pré-existentes + 23 novos), nenhuma regressão; criar um projeto multi-módulo com BOM a partir de um manifesto YAML funciona via API do adapter e via TUI; nenhum arquivo criado em disco quando o manifesto é inválido ou o destino já existe e não está vazio; `add_module`/demais testes existentes continuam passando sem alteração (extensões de `create_pom` são estritamente aditivas).
