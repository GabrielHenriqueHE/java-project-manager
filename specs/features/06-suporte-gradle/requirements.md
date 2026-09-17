# Feature 06 — Suporte a Gradle

## Contexto/Problema

O produto foi desenhado desde o início para ser agnóstico de build tool (modelo de domínio + `BuildToolAdapter`), mas até aqui só o `MavenAdapter` existia — a interface nunca tinha sido validada contra uma segunda implementação real. Gradle é a segunda build tool Java mais usada, e ao contrário do Maven (XML declarativo, `pom.xml`), um `build.gradle`/`build.gradle.kts` é código Groovy/Kotlin de verdade — não há um parser estrutural equivalente ao lxml para ler "dados".

## Objetivo

Um `GradleAdapter` capaz de inferir a estrutura de um projeto Gradle (single ou multi-módulo, Groovy ou Kotlin DSL) para o mesmo modelo de domínio já usado pelo Maven, permitindo importar/navegar projetos Gradle na TUI.

## Escopo

**Dentro (Fase 15 — fundação, leitura):**
- Detectar um projeto Gradle (`build.gradle`/`build.gradle.kts` e/ou `settings.gradle`/`settings.gradle.kts` na raiz).
- Inferir a árvore de módulos a partir de `settings.gradle(.kts)` (`include`) + o `build.gradle(.kts)` de cada módulo.
- Extrair `group`/`version`, plugins aplicados, e dependências (diretas e "gerenciadas" via módulo `java-platform`/`constraints{}` ou `platform(...)` externo) — de um **subconjunto convencional** da linguagem, via varredura por regex/contagem de chaves, não um parser Groovy/Kotlin de verdade. Arquivos que fogem desse subconjunto (loops, condicionais, funções customizadas montando a configuração) simplesmente não têm esses dados extraídos — sem crash, mas sem garantia de captura completa.
- Reaproveitar a mesma detecção de estrutura de diretórios já usada pelo Maven (`src/main/java` etc. — convenção idêntica entre as duas build tools).

**Fora (fases futuras):**
- Qualquer mutação (`add_module`, `update_dependency`, etc.) — todos os métodos de escrita da interface são stubs `NotImplementedError` nesta fase, mesmo padrão usado pelo `MavenAdapter` na sua própria Fase 1.
- Version catalogs (`gradle/libs.versions.toml`) e blocos `allprojects{}`/`subprojects{}` (herança de configuração entre módulos) — não são lidos nesta fase.
- Diretórios de fonte customizados via `sourceSets{}` — mecanismo próprio do Gradle, diferente do `build-helper-maven-plugin`; fora de escopo.
- Árvore de módulos aninhada de verdade — todo projeto incluído via `settings.gradle` é modelado como filho direto do módulo raiz nesta fase, mesmo que o path Gradle tenha mais de um segmento (`:modulos:core`); ver `design.md` da fase para o motivo.

## User stories

- Como usuário com um projeto Gradle (Groovy ou Kotlin DSL), quero importar/navegar sua estrutura na mesma TUI já usada para projetos Maven.

## Critérios de aceite

- Dado um projeto Gradle multi-módulo com `settings.gradle(.kts)` + um `build.gradle(.kts)` por módulo, quando inferido, então a árvore completa de módulos aparece, com `group`/`version`/dependências extraídos corretamente para ambos os dialetos (Groovy e Kotlin DSL).
- Dado um módulo com o plugin `java-platform` e um bloco `constraints{}`, quando inferido, então suas entradas aparecem como dependências gerenciadas (`managed=True`), no mesmo formato usado pelo BOM Maven.
- Dado um projeto raiz sem nenhum `build.gradle(.kts)` (aggregator puro, só `settings.gradle`), quando inferido, então o módulo raiz ainda é montado corretamente (packaging `pom`, sem group/version).
- Dado um módulo incluído em `settings.gradle` sem `build.gradle(.kts)` correspondente, quando inferido, então levanta um erro claro em vez de modelar um módulo incompleto silenciosamente.

## Dependências de outras features

- Reaproveita [[04-estrutura-de-diretorios]] (mesma convenção de diretórios, agora extraída para `manager.adapters.common.directory`, compartilhada entre Maven e Gradle).
