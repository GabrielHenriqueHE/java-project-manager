# Fase 1 — Fundação — Design

## Modelo de domínio (`src/manager/models.py`)

- `Dependency`: group_id, artifact_id, version opcional (herdado/gerenciado quando `None`), scope, type, classifier, `managed: bool`.
- `ProjectMetadata`: group_id, artifact_id, version, name, description, packaging (default `"jar"`), `properties: dict[str, str]`.
- `DirectoryNode` (recursivo: name, role, children) + `DirectoryStructure` (convention, source_dirs, test_dirs, resource_dirs, test_resource_dirs, tree opcional).
- `BuildFile`: path do arquivo de build do módulo.
- `Module` (recursivo via `submodules: list[Module]`): name, relative_path, metadata, dependencies, directory_structure, build_file, is_bom.
- `Project`: name, build_tool, root_path, root_module, managed_dependencies.

**Persistência**: nenhum manifesto próprio. Modelo sempre derivado ao vivo via `infer_structure()`. Único estado persistente é o registry de projetos conhecidos (`~/.config/java-project-manager/registry.json`), responsabilidade de `services/registry.py`, fora do modelo de domínio.

## Camada de Adapter (`src/manager/adapters/`)

- `base.py`: `BuildToolAdapter` (ABC) com `detect`, `infer_structure`, `add_module`, `remove_module`, `update_dependency`, `update_metadata`; `DependentModuleConflict(module_name, dependents)`.
- `maven/parser.py`: `MavenPomParser` — parse de um `pom.xml` isolado via lxml (namespace-aware), extrai metadata/deps/módulos filhos.
- `maven/adapter.py`: `MavenAdapter(BuildToolAdapter)` — `infer_structure` percorre recursivamente a árvore de poms usando o parser, monta `Project`/`Module`, marca `is_bom`; mutações ficam `NotImplementedError("Fase 2")`.

**lxml** escolhido sobre `xml.etree.ElementTree` por: suporte a namespace do Maven POM, preservação de formatação/comentários (minimiza diffs em arquivos versionados do usuário), XPath completo.

## Camada de serviços (`src/manager/services/`)

- `registry.py`: `ProjectRegistry` (load/save/add/remove) sobre JSON em `~/.config/java-project-manager/registry.json`.
- `adapters_registry.py`: `detect_adapter(path) -> BuildToolAdapter | None`, iterando os adapters conhecidos e chamando `.detect()`.

Screens nunca tocam arquivos diretamente — sempre via `services/` ou `adapters/`.

## Scaffold Textual

- `app.py`: `ManagerApp(App)`, ponto de entrada, `main()`.
- `screens/dashboard.py`: lista projetos do registry; ação "Importar".
- `screens/import_project.py`: input de path → `detect_adapter` → `infer_structure` → preview → confirma e registra.
- `screens/project_detail.py`: árvore de módulos + metadados/dependências/estrutura, somente leitura.
- `screens/widgets/project_tree.py`: `Tree` widget renderizando `Module.submodules` recursivamente.

Navegação: Dashboard → Importar → Project Detail (leitura). Telas de edição de módulo/estrutura ficam para a Fase 2 (não criadas ainda, para não sugerir escopo maior que o combinado).

## Packaging e dependências

- `[build-system]` com `hatchling`, `packages = ["src/manager"]` (corrige o projeto de "virtual" para instalável).
- `[project.scripts] jpm = "manager.app:main"`.
- Runtime: `textual`, `lxml`. Dev: `pytest`, `pytest-asyncio`, `textual-dev`.
