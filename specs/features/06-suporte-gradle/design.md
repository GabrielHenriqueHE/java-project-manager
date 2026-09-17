# Feature 06 — Suporte a Gradle — Design

## Visão geral da solução

`GradleAdapter` implementa `BuildToolAdapter` ao lado de `MavenAdapter`, registrado em `services/adapters_registry.py`. Como `build.gradle`/`build.gradle.kts` é código (Groovy/Kotlin), não dados estruturados, não existe um parser confiável de propósito geral em Python sem trazer um runtime Groovy/Kotlin inteiro — inviável para este projeto. A solução é ler um **subconjunto convencional** da linguagem via regex + contagem de chaves (para lidar com blocos aninhados como `dependencies { constraints { ... } }`), suficiente para o caso de uso real (projetos Java multi-módulo convencionais), documentando explicitamente onde a fidelidade para.

## Modelo de domínio envolvido

Nenhuma mudança — `Project`/`Module`/`Dependency`/`ProjectMetadata`/`DirectoryStructure` já eram agnósticos de build tool por design (decisão #3 do overview). O ponto de validação real dessa decisão é justamente conseguir preencher o mesmo modelo a partir de uma fonte completamente diferente (código Groovy/Kotlin em vez de XML), sem precisar de nenhum campo nem tipo novo.

## Mapeamento de conceitos Gradle → modelo de domínio

| Conceito Gradle | Campo do domínio |
|---|---|
| Nome do diretório do projeto incluído (`settings.gradle`) ou `rootProject.name` | `Module.name`/`ProjectMetadata.artifact_id` (Gradle não tem um "artifactId" explícito por módulo como o Maven; é sempre derivado do nome/diretório) |
| `group = '...'` | `ProjectMetadata.group_id` |
| `version = '...'` | `ProjectMetadata.version` |
| Plugin `java-platform` | `ProjectMetadata.packaging = "pom"` (equivalente ao BOM Maven) |
| Plugin `java`/`java-library`/`application` | `ProjectMetadata.packaging = "jar"` |
| Nenhum plugin reconhecido (aggregator puro) | `ProjectMetadata.packaging = "pom"` |
| `constraints { api 'g:a:v' }` (dentro de um módulo `java-platform`) | `Dependency(managed=True)` |
| `<config> platform('g:a:v')` com coordenada externa literal | `Dependency(managed=True)` (mesmo papel do `<dependency><scope>import</scope>` do Maven) |
| `<config> 'g:a:v'` / `<config>("g:a:v")` comum | `Dependency(managed=False, scope=<mapeado da config>)` |
| `<config> project(':x')` / `':x'` | Ignorado — não é uma coordenada externa, não vira `Dependency` |

Mapeamento config→scope: `implementation`/`api`→`compile`, `compileOnly`/`annotationProcessor`→`provided`, `runtimeOnly`→`runtime`, `test*`→`test`. Aproximado (Gradle tem granularidade que Maven/`DependencyScope` não modelam, ex. a diferença entre `implementation` e `api`), mas suficiente para visualização.

## Reaproveitamento entre adapters

`detect_directory_structure`/`STANDARD_DIRS` foram extraídos de `manager.adapters.maven.directory` para `manager.adapters.common.directory` (a convenção `src/main/java` etc. é idêntica entre o plugin `java` do Gradle e o Maven — não é uma convenção "do Maven" que o Gradle por acaso também segue, é a convenção-padrão do ecossistema Java que ambas as build tools adotam por default). `maven/directory.py` e `gradle/directory.py` reexportam de lá; `merge_registered_directories` (ligado ao `build-helper-maven-plugin`) continua exclusivo do Maven.

## Impacto na camada Textual

Nenhum — todos os painéis já operam sobre o modelo de domínio genérico. `ImportProjectScreen`/`CloneProjectScreen` já usavam `detect_adapter` (agnóstico); passam a funcionar para Gradle sem nenhuma mudança de código, só por `GradleAdapter` estar registrado.

## Alternativas consideradas e descartadas

- Rodar `gradle properties`/um init-script Gradle real para extrair metadados via a própria ferramenta (fonte de verdade perfeita) — descartado nesta fase por exigir Gradle instalado e um daemon rodando só para *ler* um projeto (custo alto para a operação mais barata do produto, `infer_structure`, que hoje roda em milissegundos para Maven); pode ser revisitado numa fase futura se a fidelidade do parser regex se mostrar insuficiente na prática.
- Dependência de um parser Groovy/Kotlin real (ex. via um subprocess Kotlin ou uma lib de parsing) — descartado por peso/complexidade desproporcional ao subconjunto de sintaxe que realmente aparece em projetos Java multi-módulo convencionais.
