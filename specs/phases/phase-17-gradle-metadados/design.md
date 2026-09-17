# Fase 17 — Gradle: Metadados — Design

## Reaproveitamento: `manager/adapters/common/lookup.py`

`find_parent`, `find_bom_module`, `find_dependents` e `find_managed_dependency_owner` eram métodos privados de `MavenAdapter` — busca em árvore pura sobre `Module`/`Dependency`, nada específico de Maven. Extraídos como funções livres, mesmo padrão da Fase 16. `MavenAdapter` mantém os métodos privados como wrappers finos (`return find_parent(...)`, etc.) para não tocar nenhum dos ~13 call sites existentes — zero mudança de comportamento.

`GradleAdapter` vai usar essas funções diretamente nas fatias seguintes (Fase 19+, remoção de dependência/módulo). Como a árvore Gradle é achatada (Fase 15: todo módulo incluído é filho direto da raiz), `find_parent` para um módulo não-raiz sempre devolve `project.root_module` — comportamento correto sem nenhum caso especial, o walk genérico já resolve isso.

## `gradle/parser.py`: promovendo a gramática compartilhada

`find_block`, `CONFIG_NAMES`, `CONFIG_TO_SCOPE`, `split_coordinate`, `DEP_LINE_RE`, `PLUGIN_ID_RE`, `ROOT_NAME_RE`, `INCLUDE_RE`, `QUOTED_RE` deixam de ser privados (`_`) — passam a ser a "gramática" pública do dialeto Gradle suportado, usada tanto por quem lê (`parse_build_file`/`parse_settings_file`) quanto por quem escreve (`GradleWriter`). Renomear só remove o `_`; nenhuma regex ou lógica muda — `test_gradle_parser.py`/`test_gradle_adapter_infer.py` continuam verdes sem alteração.

Isso é importante para o "round-trip" ficar garantido por construção: o `GradleWriter` nunca inventa uma sintaxe nova — ele monta texto usando exatamente os mesmos padrões que o parser sabe ler de volta.

## `GradleWriter` — edição textual cirúrgica

Sem uma AST Groovy/Kotlin real (decisão da Fase 15), a escrita é feita por regex/substituição de texto pontual — o mesmo espírito de "minimizar diff" do `MavenPomWriter`, mas operando em texto plano em vez de uma árvore XML. `dialect(path)`: `.kts` → Kotlin (aspas duplas, `id("x")`); senão Groovy (aspas simples, `id 'x'`) — mesma leitura frouxa do parser, mas escrita sempre idiomática por dialeto.

`set_scalar(path, name, value)`: localiza `^name\s*=?\s*['"]...['"]$` (mesmo regex de leitura do parser, adaptado para substituição) e substitui a linha inteira; se `value` for vazio, remove a linha; se não existir ainda e `value` for truthy, insere logo após o bloco `plugins{}` (ou no topo do arquivo, se não houver nenhum) — mesma posição onde os fixtures já colocam `group`/`version` na prática.

`set_packaging(path, packaging)`: opera sobre o bloco `plugins{}` (cria um do zero se não existir). Regra:
- `"pom"` → garante `java-platform` presente, remove qualquer plugin `java`/`java-library`/`application` já aplicado.
- qualquer outro valor (`"jar"` na prática) → garante ao menos um plugin da família `java` presente (só adiciona `java` se **nenhum** dos três já estiver lá — nunca troca um `java-library` existente por `java`), remove `java-platform`.

### O problema de `packaging="pom"` ser ambíguo

Ao contrário do Maven (`<packaging>pom</packaging>` é um valor XML único e barato de reescrever sempre), no Gradle `packaging` é **derivado** dos plugins (`_packaging_from_plugins`, `gradle/adapter.py`): `is_platform` → `"pom"`; `has_java_plugin` → `"jar"`; nenhum dos dois → `"pom"` também (aggregator puro, ex.: a raiz Kotlin da fixture, só um comentário, sem bloco `plugins{}`). Ou seja, `"pom"` cobre **dois estados de plugin completamente diferentes** (BOM via `java-platform` vs. aggregator sem plugin nenhum).

Se `update_metadata` chamasse `set_packaging` incondicionalmente a cada execução (como o Maven faz com `<packaging>`), qualquer chamada trivial — só mudar a `version` de um aggregator puro, por exemplo — bolaria um `java-platform` do nada, porque `set_packaging("pom")` sempre garante esse plugin presente. Decisão desta fase: `GradleAdapter.update_metadata` só passa um `packaging` para o writer quando o valor pedido **difere** do `target.metadata.packaging` atual; caso contrário passa `None`, e `GradleWriter.update_metadata` pula `set_packaging` inteiramente, deixando os plugins intocados. Isso não é uma limitação prática: uma mudança de `packaging` só faz sentido quando o usuário pede explicitamente essa mudança (mesmo padrão de "só mexe no que foi pedido" já seguido pelo `set_scalar`/`set_or_remove_scalar`).

## `GradleAdapter.update_metadata`

Mesmos guards do Maven, com uma adaptação e uma remoção:
1. `find_module` (`ValueError` se ausente).
2. `artifactId` imutável (idêntico).
3. packaging/BOM/submódulos: `metadata.packaging != "pom" and metadata.packaging != target.metadata.packaging and (target.submodules or target.is_bom)` (idêntico — pequena duplicação de lógica em vez de extrair para `common/`, aceitável para uma condição de 3 termos usada só aqui e no Maven).
4. **Removido**: a lógica de herança de `group`/`version` do pai (Maven precisa decidir "escrever explícito só se diferir do `<parent>`"; Gradle não tem essa noção — `group`/`version` são sempre escritos literalmente, incluindo `None` removendo a linha).
5. **Novo**: se `target.build_file.path.name` for `settings.gradle`/`settings.gradle.kts` (caso do módulo raiz sem build file próprio, Fase 15), levanta `ValueError` — não há onde escrever.

## Testes

`tests/test_gradle_adapter_update_metadata.py`: troca de `group`/`version` (ambos os dialetos, parametrizado), limpar campos, rejeição de rename de `artifactId`, rejeição de troca de packaging em módulo BOM e em módulo com submódulos, troca de packaging `jar→pom` (fixture `core`) e `pom→jar` (projeto sintético em `tmp_path` — nenhum módulo das fixtures compartilhadas está no estado "packaging pom, não é BOM, sem submódulos", já que `bom` é BOM e a raiz tem submódulos), packaging inalterado não mexe em plugins (fixture raiz Kotlin, aggregator puro), guard do módulo sem build file (raiz Groovy), e resultado batendo com uma reinferência do zero.
