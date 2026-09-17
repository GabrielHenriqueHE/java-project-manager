# Fase 21 — Gradle: Adicionar Módulo — Requirements

Sétima fatia de [[06-suporte-gradle]]: `GradleAdapter.add_module`. Primeira mutação que precisa criar um `build.gradle(.kts)` do zero (as fatias anteriores só editavam arquivos já existentes).

## Escopo desta fatia

**Dentro:**
- `GradleWriter.create_build_file(path, packaging, group_id, version, dependencies)`: monta um `build.gradle`/`build.gradle.kts` novo, mesma ordem de seções das fixtures (`plugins{}`, `group`/`version`, `dependencies{}` com `constraints{}` para as gerenciadas).
- `GradleWriter.add_include(path, artifact_id)`: registra o novo módulo em `include(...)` no `settings.gradle(.kts)` — anexa à lista existente ou cria a declaração do zero.
- `GradleAdapter.add_module(project, module, *, parent_name=None)`: cria o diretório/arquivos do módulo e o registra em `include(...)`.

**Fora — decisão consciente, não reabre a Fase 15:**
- Aninhamento real de módulos. A árvore Gradle é achatada por design desde a Fase 15 (todo módulo incluído é filho direto da raiz). `add_module` só aceita `parent_name=None` ou o nome do próprio módulo raiz; qualquer outro valor levanta `ValueError` em vez de tentar simular um pai intermediário que a árvore não modela.

## Critérios de aceite

- Dado um projeto Gradle (Groovy ou Kotlin), quando `add_module` é chamado com um `Module` novo, então: o diretório e a estrutura de diretórios-padrão são criados em disco; um `build.gradle(.kts)` novo existe com o packaging/group/version/dependências pedidos; o `settings.gradle(.kts)` passa a incluir o novo módulo; `infer_structure` volta a encontrá-lo.
- O dialeto do novo `build.gradle(.kts)` acompanha o do `settings.gradle(.kts)` já existente no projeto (Kotlin se `.kts`, Groovy senão) — nunca o inverso.
- `parent_name` diferente de `None`/raiz levanta `ValueError` claro.
- Nome de módulo duplicado, diretório já existente, ou pai desconhecido levantam `ValueError` (mesmas mensagens do Maven onde aplicável).
- Projeto sem `settings.gradle(.kts)` (só um `build.gradle` single-module) levanta `ValueError` — não há onde registrar o `include`.

## Definição de pronto

`uv run pytest` verde; `test_gradle_adapter_stubs.py` sem o caso de `add_module`.
