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

## Bug encontrado e corrigido após a conclusão da fase

`_validate_maven_manifest` tinha uma regra "no máximo um módulo BOM" (rejeitava `create_project` com `ValueError: Mais de um modulo BOM...` se mais de um módulo tivesse `packaging=pom` + alguma dependência `managed=True`). Reportado pelo usuário ao exportar um projeto (Fase 7) e tentar recriá-lo: um projeto real tipicamente tem o **root** importando um BOM externo via `scope=import` (ex.: `spring-boot-dependencies`) *além* do próprio submódulo BOM interno do projeto — as duas coisas são módulos `packaging=pom` com alguma dependência `managed=True`, mas Maven não proíbe isso; a regra era uma invenção desta fatia sem correspondência real. A justificativa original ("o domínio assume um único BOM, `_find_bom_module` retorna o primeiro encontrado") estava errada: `_find_bom_module` é tolerante por design (pega o primeiro, usado só para escolher **um** alvo em `remove_module`/`remove_dependency`), nunca foi uma invariante de unicidade que a criação devesse impor como erro. Corrigido removendo a checagem de contagem inteiramente (`bom_count` removido de `_validate_maven_manifest`) — nenhuma outra parte de `_materialize`/`create_pom` dependia dela. Teste de regressão: `test_create_project_allows_more_than_one_pom_module_with_managed_dependencies` (substitui o antigo `test_create_project_rejects_more_than_one_bom_module`, que testava o comportamento errado).
