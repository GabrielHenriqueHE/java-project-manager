# Fase 18 — Gradle: Dependências — Design

## Edição de blocos aninhados sem aritmética de offset absoluto

`dependencies{}` pode conter um `constraints{}` aninhado — exatamente o problema que o parser já resolveu na Fase 15 (`find_block` com contagem de chaves). Para escrever, o desafio extra é que uma mutação pode precisar tocar o conteúdo de um bloco aninhado (`constraints{}`) preservando o bloco externo (`dependencies{}`) e todo o resto do arquivo intacto.

Solução: `GradleWriter._replace_block_content(text, name, transform)` isola o conteúdo do primeiro bloco `name { ... }`, aplica `transform(conteudo) -> novo_conteudo` (uma função pura sobre uma string independente) e remonta `header + novo_conteudo + closing` no lugar do bloco original — o resto de `text` nunca é tocado. Como `transform` só enxerga o conteúdo como uma substring isolada, ele pode chamar `_replace_block_content` de novo internamente para mexer num bloco *dentro* desse conteúdo (`constraints{}` dentro de `dependencies{}`) sem nenhuma conta de índice absoluto — cada nível de aninhamento resolve seu próprio recorte e devolve uma string nova, remontada de fora para dentro. Retorna `None` (em vez de chamar `transform`) quando o bloco não existe, para quem chama decidir como criá-lo do zero.

## Upsert de uma linha de dependência

`_upsert_dep_line_in_text(text, dialect, dependency, config, indent, exclude_span=None)`: varre `text` com uma versão "linha inteira" do `DEP_LINE_RE` do parser (`_FULL_DEP_LINE_RE`, mesma gramática de coordenada/config, mas consumindo até o fim da linha — parênteses de fechamento e `\n` inclusos — para poder substituir a linha inteira, não só o trecho que o parser precisa capturar para leitura). Compara cada match por `(group_id, artifact_id)` via `split_coordinate` (mesma função do parser); se achar, substitui a linha inteira; senão, anexa uma linha nova ao final de `text`. `exclude_span` pula matches dentro de um intervalo (usado para a busca de dependência **direta** ignorar linhas que estejam dentro de `constraints{}` — do contrário uma dependência gerenciada e uma direta com o mesmo `group:artifact` se confundiriam).

- **Direta** (`_upsert_direct_line`): `exclude_span` = o span de `constraints{}` dentro do `dependencies{}`, se existir. Config vem de `dependency.scope` via `_SCOPE_TO_CONFIG` (mapa aproximado, mesmo espírito de `CONFIG_TO_SCOPE` do lado de leitura — Gradle tem mais granularidade que `DependencyScope` modela; `None`/valor desconhecido cai em `implementation`).
- **Gerenciada** (`_upsert_managed_line`): opera dentro do conteúdo de `constraints{}` via `_replace_block_content` recursivo; se `constraints{}` não existir ainda, cria o bloco do zero (`    constraints {\n<linha>    }\n`) anexado ao final do conteúdo de `dependencies{}`. Config sempre `api` (única convenção usada nas duas fixtures/dialetos).

`upsert_dependency(path, dependency)` orquestra tudo: se `dependencies{}` não existir no arquivo, cria o bloco inteiro do zero (chamando a mesma função de transformação com conteúdo inicial `""`, então ela já decide corretamente se cria `constraints{}` também, no caso gerenciado).

## Testes

`tests/test_gradle_adapter_update_dependency.py`: adicionar gerenciada nova (ambos os dialetos, parametrizado), atualizar gerenciada existente in-place (sem duplicar), atualizar direta existente in-place, criar `dependencies{}` do zero (projeto sintético em `tmp_path`, já que nenhum módulo das fixtures compartilhadas está sem esse bloco), adicionar direta nova, mapeamento de `scope`→config (`provided`→`compileOnly`), todas as rejeições espelhando o Maven, guard de módulo sem build file (Fase 17), e resultado batendo com reinferência do zero.
