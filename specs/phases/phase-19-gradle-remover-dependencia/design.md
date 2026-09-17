# Fase 19 — Gradle: Remover Dependência Gerenciada — Design

## Remoção com colapso em cascata, sem `_replace_block_content`

Diferente do upsert (Fase 18), a remoção precisa saber **se algo foi removido** (para devolver `bool`, mesmo contrato de `MavenPomWriter.remove_managed_dependency`) e decidir **depois do fato** se um bloco ficou vazio o suficiente para desaparecer inteiro. Isso não encaixa direto no `transform(str) -> str` de `_replace_block_content` (que não tem como sinalizar "nada mudou" nem re-decidir a forma do bloco externo depois de editar o interno). Por isso `remove_managed_dependency` faz a decomposição manualmente, mas reaproveitando a mesma técnica de header/conteúdo/fechamento:

1. Isola `dependencies{}` (header/conteúdo/fechamento).
2. Dentro do conteúdo, isola `constraints{}` do mesmo jeito.
3. Remove a linha de dentro do conteúdo de `constraints{}` (`_remove_dep_line`, mesma varredura por `_FULL_DEP_LINE_RE` + `split_coordinate` do upsert, mas removendo em vez de substituir). Se não achou, retorna `False` sem tocar no arquivo.
4. Se o que sobrou de `constraints{}` for só espaço em branco, remove o bloco `constraints{}` inteiro (cabeçalho+conteúdo+fechamento) de dentro do conteúdo de `dependencies{}`; senão, remonta `constraints{}` com o conteúdo novo.
5. Repete o mesmo raciocínio um nível acima: se o que sobrou de `dependencies{}` for só espaço em branco, remove o bloco `dependencies{}` inteiro do arquivo; senão, remonta normalmente.

`_remove_span_and_collapse_blank_lines(text, start, end)` faz a remoção do bloco e colapsa a sequência de linhas em branco que sobra (`\n\n\n` → `\n\n`) — puramente cosmético, o parser não se importa com espaçamento, mas evita um arquivo com blocos de linhas em branco crescendo a cada remoção.

## `GradleAdapter.remove_dependency`

Idêntico em estrutura ao Maven: usa `find_managed_dependency_owner` (função livre de `common/lookup`, Fase 17) para achar o módulo dono em qualquer lugar da árvore — `ValueError` se nenhum módulo declarar essa dependência gerenciada.

## Testes

`tests/test_gradle_adapter_remove_dependency.py`: remoção simples (ambos os dialetos), resultado batendo com reinferência, remover as duas últimas entradas colapsa `constraints{}`**e** `dependencies{}` (assertado no texto do arquivo, não só via `infer_structure`), dependência inexistente rejeitada, não mexe numa dependência **direta** de mesmas coordenadas em outro módulo (`api`→`com.example:core`), e não muta a fixture versionada.
