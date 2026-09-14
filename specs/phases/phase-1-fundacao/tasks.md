# Fase 1 — Fundação — Tasks

- [x] **T1** — Corrigir packaging: `[build-system]`/`[tool.hatch.build.targets.wheel]` em `pyproject.toml`; `uv sync`; `import manager` funcionando; `src/__init__.py` órfão removido.
- [x] **T2** — Adicionar dependências: `uv add textual lxml`; `uv add --dev pytest pytest-asyncio textual-dev`.
- [x] **T3** — Criar estrutura de `specs/` (overview + 5 features + phase-1-fundacao) com conteúdo real.
- [x] **T4** — Expandir `src/manager/models.py` (Dependency, ProjectMetadata, DirectoryNode, DirectoryStructure, BuildFile, Module, Project). Pronto quando `black`/`isort` rodam sem alterações pendentes e um round-trip Pydantic (`Project.model_validate(p.model_dump())`) funciona.
- [x] **T5** — Criar fixture `tests/fixtures/maven-multi-module/` (pom pai com `<modules>`, módulo `bom/pom.xml` com `dependencyManagement`, dois módulos de negócio, um dependendo do outro). Pronto quando a árvore de arquivos existe e é um XML Maven válido.
- [x] **T6** — Criar `src/manager/adapters/base.py` (`BuildToolAdapter` ABC + `DependentModuleConflict`). Pronto quando importável e com todos os métodos abstratos declarados.
- [x] **T7** — Implementar `MavenPomParser` (`src/manager/adapters/maven/parser.py`). Pronto quando extrai corretamente metadata/deps/módulos filhos de um `pom.xml` isolado da fixture.
- [x] **T8** — Implementar `MavenAdapter.infer_structure` (`src/manager/adapters/maven/adapter.py`). Pronto quando retorna `Project` com o número certo de módulos e BOM corretamente identificado contra a fixture do T5. Inclui stubs de mutação (`add_module`/`remove_module`/`update_dependency`/`update_metadata` levantando `NotImplementedError("Fase 2")`).
- [x] **T9** — Criar `services/registry.py` (`ProjectRegistry` com load/save/add/remove sobre JSON em `~/.config/java-project-manager/registry.json`).
- [x] **T10** — Criar `services/adapters_registry.py` (`detect_adapter(path)`).
- [x] **T11** — Scaffold Textual mínimo: `app.py`, `screens/dashboard.py`, `screens/import_project.py`, `screens/project_detail.py`, `screens/widgets/project_tree.py`.
- [x] **T12** — Entry point: `main()` em `app.py` + `[project.scripts]` em `pyproject.toml`; validado que `uv run jpm` funciona.
- [x] **T13** — Testes: `tests/test_maven_adapter_infer.py` (contra a fixture) e `tests/test_app_dashboard.py` (via `App.run_test()`). 18 testes, todos passando.
- [x] **T14** — Atualizar `README.md` (setup, como rodar `uv run jpm`, como rodar `uv run pytest`, link para `specs/00-overview.md`).

## Definição de pronto da fase

Todas as tasks acima marcadas; `uv run pytest` verde; `uv run jpm` abre o Dashboard, permite importar a fixture, e `ProjectDetailScreen` mostra a árvore de módulos e metadados corretamente; o projeto importado persiste no `registry.json` entre reaberturas da app.
