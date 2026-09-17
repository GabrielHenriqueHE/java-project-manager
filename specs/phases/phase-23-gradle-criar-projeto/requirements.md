# Fase 23 — Gradle: Criar Projeto — Requirements

Nona fatia de [[06-suporte-gradle]], última mutação em escopo: `GradleAdapter.create_project`. Fecha a feature — depois desta fatia, todas as mutações que fazem sentido no modelo Gradle atual estão implementadas.

## Escopo desta fatia

**Dentro:**
- `GradleAdapter.create_project(manifest, destination_path, source_root=None)`: materializa `settings.gradle` (raiz + `include(...)` achatado, um nível — mesma árvore achatada da Fase 15) e um `build.gradle` por módulo, reaproveitando `GradleWriter.create_build_file` (Fase 21) para cada arquivo.
- `_validate_gradle_manifest`: mesmas validações estruturais do Maven (`_validate_maven_manifest`) **menos** a exigência de `groupId`/`version` no módulo raiz — regra que só existe no Maven porque o pom raiz não tem `<parent>` de quem herdar; o Gradle nunca leu herança nenhuma (nem de `allprojects{}`), então group/version ausentes na raiz não são erro, só ficam de fora do `build.gradle`.
- Materialização de diretórios (com suporte a `source_root`, copiando conteúdo real como no Maven) — sem nenhuma tentativa de "registrar" diretório customizado no build, já que o mecanismo equivalente (`sourceSets{}`) está fora de escopo desta feature inteira.

**Fora — decisões conscientes, não reabrem nada sem justificativa nova:**
- **Dialeto**: `ModuleManifest` é agnóstico de build tool desde a Fase 6 e não carrega nenhuma informação de dialeto Gradle. `create_project` sempre materializa em Groovy (`build.gradle`/`settings.gradle`). Adicionar um campo de dialeto ao manifesto reabriria uma decisão de arquitetura da Fase 6 — não foi pedido, então não foi feito.
- **Aninhamento além de um nível**: mesma limitação de `add_module` (Fase 21) — a árvore Gradle é achatada por design desde a Fase 15. Um manifesto com netos (submódulo de submódulo) não é suportado; todo `ModuleManifest.submodules` do nó raiz vira `include(...)` direto, e submódulos de segundo nível em diante simplesmente não são materializados nesta fase (mesmo escopo que o `MavenAdapter` já testa — só um nível, raiz → filhos diretos).
- **Registro de diretório customizado no build**: como em toda a feature, fora de escopo (`sourceSets{}`).

## Critérios de aceite

- Dado um manifesto de um único módulo, `create_project` cria `build.gradle`+`settings.gradle` na raiz e `infer_structure` volta a encontrar o módulo com os mesmos metadados.
- Dado um manifesto multi-módulo (raiz + submódulos diretos), cada submódulo ganha seu próprio diretório/`build.gradle`, e a raiz inclui todos via `include(...)`.
- Dado um submódulo BOM (`packaging=pom` + dependência gerenciada), `is_bom` é `True` numa reinferência e a dependência aparece em `Project.managed_dependencies`.
- Dado `source_root`, os diretórios de um módulo são copiados com conteúdo real quando existir uma pasta correspondente; caso contrário, criados vazios (mesmo comportamento do Maven).
- Mesmas rejeições estruturais do Maven (nome duplicado, dependência gerenciada sem version, packaging inconsistente com submódulos/BOM, destino não-vazio) — **exceto** a exigência de group/version na raiz, que não se aplica ao Gradle.

## Definição de pronto

`uv run pytest` verde; nenhum stub restante em `GradleAdapter` além de `register_directory_role`/`unregister_directory_role` (permanentemente fora de escopo).
