# Fase 17 — Gradle: Metadados — Requirements

Terceira fatia de [[06-suporte-gradle]], segunda mutação real: `GradleAdapter.update_metadata`. Primeira fatia que precisa efetivamente editar `build.gradle(.kts)` como texto (Fase 16 só mexia em filesystem).

## Escopo desta fatia

**Dentro:**
- `GradleAdapter.update_metadata(project, module_name, metadata)`: atualiza `group`/`version` (escritos literalmente, sem lógica de herança — o parser nunca lê `allprojects{}`/`subprojects{}`, então não há "herdar do pai" a considerar aqui, diferente do Maven) e, quando o `packaging` pedido difere do atual, troca o plugin aplicado (`java-platform` para `"pom"`, um plugin da família `java`/`java-library`/`application` para `"jar"`).
- Novo `src/manager/adapters/gradle/writer.py` (`GradleWriter`), primeira peça de escrita textual para Gradle: `set_scalar`, `set_packaging`, `update_metadata`.
- Refatoração de reaproveitamento: `_find_parent`/`_find_dependents`/`_find_bom_module`/`_find_managed_dependency_owner`, antes privados em `MavenAdapter`, extraídos para `manager.adapters.common.lookup` (mesmo padrão da Fase 16 com `find_module`/`resolve_module_relative_path`) — `GradleAdapter` vai precisar deles nas fatias seguintes (remoção de módulo/dependência).
- Promoção de `_find_block`/`_CONFIG_NAMES`/`_CONFIG_TO_SCOPE`/`_split_coordinate`/`_DEP_LINE_RE`/`_PLUGIN_ID_RE`/`_ROOT_NAME_RE`/`_INCLUDE_RE`/`_QUOTED_RE` de `gradle/parser.py` para nomes públicos (mesma gramática usada por leitura e escrita).

**Fora (fatias futuras):**
- `name`/`description`/`java_version` — `GradleAdapter.infer_structure` nunca populou esses campos de `ProjectMetadata` para Gradle (nem na Fase 15, nem agora); não há o que escrever de volta, então `update_metadata` simplesmente os ignora.
- Demais mutações (`update_dependency`, `add_module`, `remove_module`, `remove_dependency`, `remove_direct_dependency`, `create_project`).

## Critérios de aceite

- Dado um módulo Gradle, quando `update_metadata` muda `group`/`version`, então o `build.gradle(.kts)` reflete os novos valores e `infer_structure` os lê de volta corretamente (ou os remove, se `None`).
- Dado um módulo com `packaging` diferente do pedido, quando `update_metadata` muda para `"pom"`, então o plugin `java-platform` passa a estar presente e qualquer plugin da família `java` é removido; o inverso vale para `"jar"`.
- Dado um módulo cujo `packaging` pedido é igual ao atual, quando `update_metadata` é chamado (por exemplo só para mudar `version`), então nenhum plugin é tocado — evita o caso em que um aggregator puro (packaging `"pom"` só por ausência de plugin) ganharia um `java-platform` do nada numa chamada que não pediu mudança de packaging.
- Dado um módulo com submódulos ou que é o BOM do projeto, quando `update_metadata` tenta mudar `packaging` para algo diferente de `"pom"`, então levanta `ValueError` (mesma regra do Maven).
- Dado o módulo raiz de um projeto Gradle sem `build.gradle(.kts)` próprio (só `settings.gradle(.kts)`), quando `update_metadata` é chamado, então levanta `ValueError` claro (não há arquivo para escrever).
- Renomear `artifactId` continua rejeitado (mesma regra do Maven).

## Definição de pronto

`uv run pytest` verde, sem regressão no `MavenAdapter` (refatoração de `_find_parent`/`_find_dependents`/`_find_bom_module`/`_find_managed_dependency_owner` é comportamentalmente neutra); `test_gradle_adapter_stubs.py` sem o caso de `update_metadata`.
