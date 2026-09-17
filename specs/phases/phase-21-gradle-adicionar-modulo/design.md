# Fase 21 — Gradle: Adicionar Módulo — Design

## `create_build_file`: reaproveitando os renderizadores já existentes

Nada novo é inventado aqui — `create_build_file` só orquestra, na ordem certa, peças que já existiam desde as Fases 17/18: `_render_plugins_block` (mesmo helper de `set_packaging`, agora chamado diretamente para montar o bloco do zero), `quote` (para `group`/`version`) e `_render_dep_line` (mesmo helper do upsert, um por dependência direta e um por gerenciada dentro de um `constraints{}` inline). A ordem das seções (`plugins{}`, blank, `group`/`version`, blank, `dependencies{}`) espelha exatamente o que as fixtures já têm, para o resultado ser indistinguível de um arquivo escrito à mão seguindo a mesma convenção.

## `add_include`: anexar ou criar

Reaproveita `INCLUDE_RE`/`QUOTED_RE` (a mesma gramática do parser, promovida a pública na Fase 17) para achar a declaração `include(...)` existente e inserir uma entrada nova na lista (sem duplicar, se já presente) — ou criar a declaração do zero se o `settings.gradle(.kts)` ainda não tiver nenhuma (caso raro, mas possível: um settings.gradle só com `rootProject.name`).

## Árvore achatada: `parent_name` só aceita a raiz

A Fase 15 decidiu deliberadamente modelar todo módulo incluído como filho direto da raiz (árvore achatada), mesmo quando o path Gradle sugere aninhamento. `add_module` respeita essa decisão sem tentar contorná-la: `parent_name=None` ou o nome da própria raiz são os únicos valores aceitos; qualquer outro nome de módulo levanta `ValueError` explicando a limitação, em vez de criar uma ilusão de suporte a hierarquia que a árvore não tem como representar depois (o próximo `infer_structure` simplesmente colocaria o módulo novo como mais um filho direto da raiz, silenciosamente "perdendo" o pai pedido — pior que um erro claro).

## Dialeto do novo módulo: acompanha o `settings.gradle(.kts)` do projeto

Um projeto multi-módulo Gradle é sempre um dialeto só (não haveria razão de negócio para misturar `.kts` e não-`.kts` entre módulos do mesmo projeto). `add_module` deriva o dialeto do `settings.gradle(.kts)` já existente (`.kts` → Kotlin, senão Groovy) em vez de aceitar um parâmetro novo — decisão consistente com a Fase 23 (`create_project`), que faz a mesma escolha pelo mesmo motivo.

## Ordem dos guards

Todos os guards (settings ausente, pai inválido, nome duplicado, diretório já existente) são checados **antes** de qualquer escrita em disco — mesmo padrão do `MavenAdapter.add_module` e de todas as fatias anteriores desta feature.

## Testes

`tests/test_gradle_adapter_add_module.py`: criação básica com diretórios (ambos os dialetos, parametrizado), dialeto do build file acompanhando o do settings (um teste por dialeto, checando a extensão do arquivo e a forma de aspas no `include`), packaging/group/version customizados, dependências iniciais (gerenciada, num módulo `pom` novo), `parent_name` não-raiz rejeitado, `parent_name` explícito igual à raiz aceito, nome duplicado/diretório existente/pai desconhecido rejeitados, e resultado batendo com reinferência.
