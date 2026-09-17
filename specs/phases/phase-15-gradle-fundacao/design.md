# Fase 15 — Gradle: Fundação (Leitura) — Design

## Estrutura de arquivos

```
src/manager/adapters/common/directory.py   # extraido de maven/directory.py (ver abaixo)
src/manager/adapters/gradle/
  adapter.py      # GradleAdapter(BuildToolAdapter)
  parser.py        # parse_build_file/parse_settings_file + toda a extracao por regex
  directory.py      # reexporta de common/, mesmo padrao de maven/directory.py
```

Um único `parser.py` cobre **os dois dialetos** (Groovy e Kotlin DSL) com o mesmo conjunto de regexes, em vez de dois parsers separados: as diferenças entre `id 'java'` (Groovy) e `id("java")` (Kotlin), ou `group = 'x'`/`group 'x'` (Groovy) vs `group = "x"` (Kotlin), são só cosméticas (aspas simples vs duplas, parênteses opcionais) — cada regex já aceita ambas as formas (`\(?...\)?`, `['"]`). Ganho real: metade do código de dois parsers quase idênticos, ao custo de regexes um pouco mais permissivas (aceitam, por exemplo, `id("x")` num arquivo `.gradle` Groovy, o que é sintaticamente válido em Groovy mesmo não sendo o idiomático).

## Extração por regex + contagem de chaves

Sem um parser Groovy/Kotlin de verdade, blocos (`plugins { ... }`, `dependencies { ... }`, `constraints { ... }`) não podem ser isolados só com regex ingênua (chaves aninhadas quebram um regex "até o primeiro `}`"). `_find_block(text, name)` localiza `name\s*\{` e então conta profundidade de chaves char a char até fechar — O(n) simples, sem dependência nova, suficiente para blocos com aninhamento arbitrário (`dependencies { constraints { ... } }`).

Dentro de `dependencies{}`, o bloco `constraints{}` (se existir) é extraído e **removido** do texto antes de rodar a regex de dependência "comum" sobre o restante — senão as mesmas linhas (`api 'g:a:v'` dentro de `constraints{}` usa as mesmas palavras-chave de configuração) seriam capturadas duas vezes, uma como gerenciada (via `constraints{}`) e outra como direta (via a regex geral rodando sobre o texto inteiro do bloco `dependencies{}`).

## Coordenadas de dependência

`_split_coordinate("group:artifact:version")` retorna `None` (e a linha é ignorada, sem virar `Dependency`) quando a string começa com `:` — esse é o formato de uma referência de projeto Gradle (`project(':core')`, ou o atalho `':core'` sem o `project(...)`), não uma coordenada Maven-like externa. Sem essa guarda, `':core'.split(':')` produziria `group_id=''`, um `Dependency` inválido/sem sentido.

## `platform(...)` — quando vira `managed=True`

Uma dependência escrita como `<config> platform('g:a:v')` (com uma coordenada *externa literal* dentro do `platform(...)`) vira `Dependency(managed=True)` — é o equivalente Gradle de importar um BOM externo (ex. `implementation platform('org.springframework.boot:spring-boot-dependencies:3.2.0')`). Já `<config> platform(project(':bom'))` (referência a outro módulo do mesmo projeto) não produz nenhum `Dependency` — cai na mesma guarda de `_split_coordinate` acima, porque `project(':bom')` nunca produz uma string "g:a:v" válida pelo regex de coordenada.

## Árvore de módulos: sempre filhos diretos da raiz

`settings.gradle(.kts)` declara a lista completa de projetos incluídos num único lugar (diferente do Maven, onde cada pom pai lista seus próprios `<modules>`, formando a árvore naturalmente por aninhamento de arquivos). Um path Gradle como `:modulos:core` **não implica** que exista um projeto `:modulos` incluído — pode ser só um diretório intermediário sem `build.gradle` próprio. Reconstruir a árvore "de verdade" exigiria inferir quais segmentos intermediários são projetos de fato (checando se cada prefixo do path também foi incluído) e tratar os demais como agrupadores puramente estruturais sem entrada em `settings.gradle`.

Decisão desta fase: **todo módulo incluído é modelado como filho direto do módulo raiz**, com `relative_path` computado pelo path Gradle inteiro (`:modulos:core` → `modulos/core`) mas sem nenhum nó intermediário `modulos` na árvore de `Module.submodules`. Para o caso majoritário (módulos declarados no nível mais alto, ex. `include 'core', 'api'`) isso é idêntico ao comportamento correto. Para hierarquias profundas customizadas, a árvore fica "achatada" mas os módulos continuam presentes e corretamente localizados em disco — trade-off aceitável para a fundação; revisitar numa fase futura só se houver demanda real.

## Módulo raiz sem `build.gradle`

Um projeto Gradle multi-módulo pode não ter nenhum `build.gradle(.kts)` na raiz (aggregator puro via `settings.gradle` sozinho) — bem mais comum no Gradle do que no Maven, onde o pom raiz é sempre obrigatório. `GradleAdapter.detect` reconhece a raiz também só por `settings.gradle(.kts)` (não exige `build.gradle`). Quando o root build file não existe: `packaging="pom"`, `group`/`version=None`, e `Module.build_file` aponta para o `settings.gradle(.kts)` em vez de um build file inexistente — ainda um arquivo real do projeto, mantendo a garantia do modelo de que todo `Module` tem um `build_file` válido.

## Packaging (`ProjectMetadata.packaging`)

Gradle não tem um conceito de "packaging" por módulo como o `<packaging>` do Maven — é inferido dos plugins aplicados: `java-platform` → `"pom"` (BOM); `java`/`java-library`/`application` → `"jar"`; nenhum desses (aggregator puro, ou módulo raiz sem build file) → `"pom"`. `is_bom` reaproveita exatamente a mesma regra já usada pelo Maven: `packaging == "pom" and bool(managed_dependencies)`.

## Módulo incluído sem build file → erro, não modelagem parcial

Coerente com a escolha "conventional subset only, erro claro em vez de adivinhar" (decisão do usuário para o parser como um todo): um módulo listado em `settings.gradle(.kts)` cujo diretório não tem `build.gradle` nem `build.gradle.kts` levanta `ValueError` explícito, em vez de ser modelado com metadados vazios/adivinhados.

## Testes

- `tests/test_gradle_parser.py` — unidade, ambos os dialetos, incluindo casos de borda (referência de projeto ignorada, `version` de plugin de terceiros não confundida com a `version` do próprio projeto, bloco `dependencies{}` ausente).
- `tests/test_gradle_adapter_infer.py` — `infer_structure` fim-a-fim contra as duas fixtures (`tests/fixtures/gradle-multi-module-groovy/`, `tests/fixtures/gradle-multi-module-kotlin/`), parametrizado onde o comportamento deveria ser idêntico entre os dois dialetos.
- `tests/test_adapters_registry.py` — `detect_adapter` roteia corretamente Maven vs Gradle (Groovy e Kotlin) vs desconhecido.
- `tests/test_gradle_adapter_stubs.py` — todo método de mutação levanta `NotImplementedError`.
- `tests/test_main_screen.py` — um teste de TUI importando um projeto Gradle real via `ImportProjectScreen`, confirmando que os painéis existentes (nenhuma mudança de código) já funcionam.

As duas fixtures foram desenhadas para exercitar os dois "branches" do módulo raiz: a fixture Groovy não tem `build.gradle` na raiz (só `settings.gradle`); a fixture Kotlin tem um `build.gradle.kts` raiz mínimo (sem plugins). Ambas espelham a fixture `maven-multi-module` existente (`bom`/`core`/`api`, mesmas coordenadas e mesma relação de dependência direta vs. gerenciada em `api`→`com.example:core`), para deixar claro que o resultado final da inferência é equivalente entre as três build tools/dialetos para o "mesmo" projeto conceitual.
