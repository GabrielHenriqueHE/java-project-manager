# Fase 20 — Gradle: Remover Dependência Direta — Design

## Um nível de aninhamento a menos que a Fase 19

`remove_dependency` (direta) só precisa isolar `dependencies{}` uma vez — não há um segundo nível de bloco a decompor, já que a busca acontece na porção de `dependencies{}` fora de `constraints{}` (via `exclude_span`, mesmo mecanismo do upsert/remoção gerenciada). Estrutura idêntica à metade externa de `remove_managed_dependency` (Fase 19): isola header/conteúdo/fechamento de `dependencies{}`, remove a linha via `_remove_dep_line` (reaproveitado, sem mudança), colapsa o bloco inteiro se o que sobrar for só espaço em branco.

## Naming: por que dois métodos diferentes no writer

`GradleWriter.remove_managed_dependency` (Fase 19) e `GradleWriter.remove_dependency` (esta fase, só direta) espelham deliberadamente o mesmo par de nomes do `MavenPomWriter` — `remove_managed_dependency` sempre busca globalmente pela árvore (dependência gerenciada pode estar em qualquer módulo `pom`), `remove_dependency` sempre recebe o módulo já resolvido (uma dependência direta pertence a um único arquivo). `GradleAdapter.remove_direct_dependency` (o método da interface pública) chama `self._writer.remove_dependency` — o nome do método do writer não precisa (nem deveria) coincidir com o nome do método da interface; o que importa é a simetria com o Maven.

## `GradleAdapter.remove_direct_dependency`

`find_module` guard, chama o writer, `ValueError` se `False` (nada encontrado) — idêntico em estrutura ao Maven.

## Testes

`tests/test_gradle_adapter_remove_direct_dependency.py`: remoção simples (ambos os dialetos), colapso do bloco `dependencies{}` quando fica vazio, resultado batendo com reinferência, não confunde com uma entrada gerenciada de mesmas coordenadas (nem no sentido "não mexe" nem no sentido "não deixa remover uma gerenciada por essa via" — o segundo caso usa `bom`/`org.apache.commons:commons-lang3`, que só existe dentro de `constraints{}`), módulo/dependência inexistentes rejeitados, fixture versionada intocada.
