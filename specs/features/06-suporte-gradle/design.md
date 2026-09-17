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

## Escrita: `GradleWriter`

Todas as mutações (Fases 16-23) passam por `GradleWriter` (`manager/adapters/gradle/writer.py`), que aplica edições textuais cirúrgicas em vez de reconstruir o arquivo inteiro — mesmo objetivo de "minimizar o diff" do `MavenPomWriter`, mas sem uma árvore de sintaxe real por baixo (decisão da Fase 15, mantida). Dois mecanismos sustentam isso:

1. **Gramática compartilhada com o parser**: `find_block`, `CONFIG_NAMES`, `CONFIG_TO_SCOPE`, `split_coordinate`, `DEP_LINE_RE`, `PLUGIN_ID_RE`, `ROOT_NAME_RE`, `INCLUDE_RE`, `QUOTED_RE` (`gradle/parser.py`) são públicos desde a Fase 17 justamente para o writer reaproveitá-los — o texto que o writer produz é sempre parseável de volta pela mesma gramática que o lê, por construção.
2. **Decomposição recursiva de blocos aninhados** (`_replace_block_content`, Fase 18): isola o conteúdo de um bloco `nome { ... }`, aplica uma transformação pura sobre essa substring, remonta cabeçalho+conteúdo+fechamento. Como a transformação só enxerga uma substring independente, ela pode chamar `_replace_block_content` de novo para tratar um bloco *dentro* dela (ex.: `constraints{}` dentro de `dependencies{}`) sem nenhuma aritmética de offset absoluto. Remoção com colapso em cascata (Fases 19/20) faz a mesma decomposição manualmente, já que precisa saber se algo mudou e redecidir a forma do bloco depois do fato — algo que uma transformação pura `str -> str` não expressa.

Um bug real surgiu exatamente na borda desse mecanismo: a regex usada para localizar/substituir uma linha de dependência inteira (`_FULL_DEP_LINE_RE`) tinha, na cauda, um `\s*` que atravessa `\n` — o primeiro match de um bloco com 2+ entradas engolia a quebra de linha e a indentação da entrada seguinte, impedindo que ela fosse encontrada em buscas subsequentes. Só apareceu na Fase 22 (`remove_module` removendo a *segunda* entrada de `constraints{}` do BOM), porque nenhum teste anterior buscava especificamente uma entrada que não fosse a primeira/única de um bloco. Corrigido trocando os `\s*` da cauda por `[ \t]*` (só espaço/tab da mesma linha).

## `sourceSets{}`: por que não foi implementado

`register_directory_role`/`unregister_directory_role` (o par que, no Maven, escreve/lê `build-helper-maven-plugin`) permanecem stub. O equivalente conceitual no Gradle é `sourceSets{}` (ex.: `sourceSets { main { java { srcDirs += 'src/main/proto' } } }`), mas ao contrário do `build-helper-maven-plugin` — uma dependência declarativa, sempre no mesmo formato — `sourceSets{}` é um bloco de configuração Groovy/Kotlin genuinamente mais livre (métodos encadeados, `+=` vs. `srcDir(...)`, múltiplas formas idiomáticas de expressar a mesma coisa), o que o afastaria do "subconjunto convencional, sem crash em código incomum" que sustenta todo o parser desde a Fase 15. Implementar escrita para `sourceSets{}` exigiria ler de volta um subconjunto bem mais amplo do que o hoje suportado, para não arriscar corromper builds reais com formas menos comuns do bloco. Ficou de fora desde o requirements da feature (não é uma "próxima fatia", é um limite permanente) — revisitar exigiria justificativa nova, não uma continuação natural do trabalho já feito.

## Impacto na camada Textual

Nenhum — nem para leitura, nem para as mutações das Fases 16-23. Todos os painéis e telas de mutação (formulários de metadados/dependência/módulo, os bindings do Painel [5]) já chamam a interface `BuildToolAdapter` genericamente, sem ramificação por build tool; `ImportProjectScreen`/`CloneProjectScreen` já usavam `detect_adapter` (agnóstico). Um projeto Gradle passou a suportar cada mutação assim que o método correspondente deixou de ser stub — nenhuma tela precisou de nenhuma mudança de código em nenhuma das nove fatias.

## Alternativas consideradas e descartadas

- Rodar `gradle properties`/um init-script Gradle real para extrair metadados via a própria ferramenta (fonte de verdade perfeita) — descartado nesta fase por exigir Gradle instalado e um daemon rodando só para *ler* um projeto (custo alto para a operação mais barata do produto, `infer_structure`, que hoje roda em milissegundos para Maven); pode ser revisitado numa fase futura se a fidelidade do parser regex se mostrar insuficiente na prática.
- Dependência de um parser Groovy/Kotlin real (ex. via um subprocess Kotlin ou uma lib de parsing) — descartado por peso/complexidade desproporcional ao subconjunto de sintaxe que realmente aparece em projetos Java multi-módulo convencionais.
