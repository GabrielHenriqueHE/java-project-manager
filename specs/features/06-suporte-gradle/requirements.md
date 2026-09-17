# Feature 06 — Suporte a Gradle

## Contexto/Problema

O produto foi desenhado desde o início para ser agnóstico de build tool (modelo de domínio + `BuildToolAdapter`), mas até aqui só o `MavenAdapter` existia — a interface nunca tinha sido validada contra uma segunda implementação real. Gradle é a segunda build tool Java mais usada, e ao contrário do Maven (XML declarativo, `pom.xml`), um `build.gradle`/`build.gradle.kts` é código Groovy/Kotlin de verdade — não há um parser estrutural equivalente ao lxml para ler "dados".

## Objetivo

Um `GradleAdapter` capaz de inferir a estrutura de um projeto Gradle (single ou multi-módulo, Groovy ou Kotlin DSL) para o mesmo modelo de domínio já usado pelo Maven, e de aplicar as mesmas mutações que o `MavenAdapter` oferece (metadados, dependências, módulos, criação de projeto) editando `build.gradle(.kts)`/`settings.gradle(.kts)` como texto — sem exigir um runtime Groovy/Kotlin instalado.

## Escopo

**Dentro:**
- **Leitura** (Fase 15 — fundação): detectar um projeto Gradle (`build.gradle`/`build.gradle.kts` e/ou `settings.gradle`/`settings.gradle.kts` na raiz); inferir a árvore de módulos a partir de `settings.gradle(.kts)` (`include`) + o `build.gradle(.kts)` de cada módulo; extrair `group`/`version`, plugins aplicados, e dependências (diretas e "gerenciadas" via módulo `java-platform`/`constraints{}` ou `platform(...)` externo) — de um **subconjunto convencional** da linguagem, via varredura por regex/contagem de chaves, não um parser Groovy/Kotlin de verdade. Arquivos que fogem desse subconjunto (loops, condicionais, funções customizadas montando a configuração) simplesmente não têm esses dados extraídos — sem crash, mas sem garantia de captura completa. Reaproveita a mesma detecção de estrutura de diretórios já usada pelo Maven (`src/main/java` etc. — convenção idêntica entre as duas build tools).
- **Escrita** (Fases 16-23): `add_directory`/`remove_directory` (filesystem puro, sem editar build file); `update_metadata` (group/version literais, sem herança; troca de plugin para mudar packaging); `update_dependency`/`remove_dependency`/`remove_direct_dependency` (upsert/remoção em `dependencies{}`/`constraints{}`, com colapso em cascata de blocos vazios); `add_module`/`remove_module` (cria/remove `build.gradle(.kts)` + entrada em `include(...)`, só filhos diretos da raiz); `create_project` (materializa um projeto inteiro a partir de um `ModuleManifest`, sempre Groovy). Toda a escrita é feita por `GradleWriter` (`manager/adapters/gradle/writer.py`) via edição textual cirúrgica — mesma filosofia de "minimizar o diff" do `MavenPomWriter`, mas sem uma árvore de sintaxe real por baixo, reaproveitando a mesma gramática (regex/`find_block`) que o parser usa para ler.

**Fora — permanente, não uma fatia pendente:**
- `register_directory_role`/`unregister_directory_role` — o mecanismo equivalente no Gradle é `sourceSets{}`, deliberadamente não implementado (ver `design.md`).
- Version catalogs (`gradle/libs.versions.toml`) e blocos `allprojects{}`/`subprojects{}` (herança de configuração entre módulos) — nunca lidos nem escritos.
- Árvore de módulos aninhada de verdade — todo projeto incluído via `settings.gradle` é modelado como filho direto do módulo raiz, mesmo que o path Gradle tenha mais de um segmento (`:modulos:core`); consequência direta: `add_module`/`create_project` só suportam um nível (raiz → filhos diretos).
- Dialeto Kotlin DSL em `create_project` — o `ModuleManifest` é agnóstico de build tool (Fase 6) e não carrega essa informação; `create_project` sempre materializa em Groovy.

## User stories

- Como usuário com um projeto Gradle (Groovy ou Kotlin DSL), quero importar/navegar sua estrutura na mesma TUI já usada para projetos Maven.
- Como usuário com um projeto Gradle, quero editar metadados, dependências e módulos pela mesma TUI, sem precisar editar `build.gradle(.kts)` na mão.

## Critérios de aceite

- Dado um projeto Gradle multi-módulo com `settings.gradle(.kts)` + um `build.gradle(.kts)` por módulo, quando inferido, então a árvore completa de módulos aparece, com `group`/`version`/dependências extraídos corretamente para ambos os dialetos (Groovy e Kotlin DSL).
- Dado um módulo com o plugin `java-platform` e um bloco `constraints{}`, quando inferido, então suas entradas aparecem como dependências gerenciadas (`managed=True`), no mesmo formato usado pelo BOM Maven.
- Dado um projeto raiz sem nenhum `build.gradle(.kts)` (aggregator puro, só `settings.gradle`), quando inferido, então o módulo raiz ainda é montado corretamente (packaging `pom`, sem group/version).
- Dado um módulo incluído em `settings.gradle` sem `build.gradle(.kts)` correspondente, quando inferido, então levanta um erro claro em vez de modelar um módulo incompleto silenciosamente.
- Dado qualquer uma das mutações em escopo, quando aplicada, então o resultado é lido de volta corretamente por `infer_structure` (round-trip), em ambos os dialetos onde a mutação edita um arquivo já existente.

## Dependências de outras features

- Reaproveita [[04-estrutura-de-diretorios]] (mesma convenção de diretórios, agora extraída para `manager.adapters.common.directory`, compartilhada entre Maven e Gradle).
