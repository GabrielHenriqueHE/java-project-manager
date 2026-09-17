# Feature 06 — Suporte a Gradle — Tasks

**Fundação (leitura) implementada** na Fase 15 (`specs/phases/phase-15-gradle-fundacao/`): `GradleAdapter.detect`/`infer_structure`, Groovy e Kotlin DSL, árvore de módulos + group/version + dependências (diretas e gerenciadas via `java-platform`/`constraints{}` ou `platform(...)` externo) extraídos por um parser baseado em regex + contagem de chaves (subconjunto convencional da linguagem). Registrado em `services/adapters_registry.py`; nenhuma mudança na TUI foi necessária.

**Todas as mutações em escopo implementadas** nas Fases 16-23, cada uma sua própria fatia (`specs/phases/phase-<n>-gradle-*/`):

- **Fase 16 — Diretórios**: `add_directory`/`remove_directory` — filesystem puro, sem editar build file. `find_module`/`resolve_module_relative_path` extraídos para `manager.adapters.common.lookup`.
- **Fase 17 — Metadados**: `update_metadata`. Primeiro `GradleWriter` (`set_scalar`, `set_packaging`); `find_parent`/`find_bom_module`/`find_dependents`/`find_managed_dependency_owner` extraídos para `common/lookup`; gramática do parser (`find_block`, `CONFIG_NAMES` etc.) promovida a pública.
- **Fase 18 — Dependências**: `update_dependency` (upsert direta/gerenciada). `GradleWriter._replace_block_content`, decomposição recursiva de blocos aninhados.
- **Fase 19 — Remover Dependência Gerenciada**: `remove_dependency`, com colapso em cascata de `constraints{}`/`dependencies{}`.
- **Fase 20 — Remover Dependência Direta**: `remove_direct_dependency`, mesmo colapso só na porção direta.
- **Fase 21 — Adicionar Módulo**: `add_module`, cria `build.gradle(.kts)` do zero (`GradleWriter.create_build_file`) + `include(...)` (`add_include`). Só filhos diretos da raiz.
- **Fase 22 — Remover Módulo**: `remove_module`, espelhando o Maven; `remove_include`. Corrigido um bug latente em `_FULL_DEP_LINE_RE` (vazamento entre linhas num bloco com 2+ dependências).
- **Fase 23 — Criar Projeto**: `create_project`, materializa `settings.gradle` + um `build.gradle` por módulo a partir de um `ModuleManifest`, sempre Groovy, reaproveitando `create_build_file` integralmente.

**Fora de escopo, permanente** (não são fatias pendentes — ver `requirements.md`/`design.md`): `register_directory_role`/`unregister_directory_role` (`sourceSets{}` exigiria ler um subconjunto da linguagem bem mais amplo do que o hoje suportado); version catalogs (`gradle/libs.versions.toml`); `allprojects{}`/`subprojects{}`; árvore de módulos verdadeiramente aninhada (hoje achatada sob a raiz — consequência direta, `add_module`/`create_project` só suportam um nível); dialeto Kotlin DSL em `create_project` (o `ModuleManifest` não carrega essa informação).
