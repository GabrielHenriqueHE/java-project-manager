# Fase 15 — Gradle: Fundação (Leitura) — Requirements

Primeira fatia de [[06-suporte-gradle]]: só `detect`/`infer_structure`, mesmo escopo da `phase-1-fundacao` do Maven (modelo + inferência, TUI em modo leitura via a infraestrutura já existente — nenhuma mudança na TUI é necessária, ela já é agnóstica).

## Escopo desta fatia

**Dentro:**
- `GradleAdapter.detect`/`infer_structure`, Groovy e Kotlin DSL.
- Extração de: árvore de módulos (via `settings.gradle(.kts)` + `include`), `group`/`version`, plugins, dependências diretas e gerenciadas (`java-platform`/`constraints{}` + `platform(...)` externo).
- Detecção de estrutura de diretórios (reaproveitando a mesma convenção do Maven, extraída para um módulo compartilhado).
- Registro em `services/adapters_registry.py`.

**Fora:** todas as mutações (stubs `NotImplementedError`); version catalogs; `allprojects{}`/`subprojects{}`; `sourceSets{}` customizado; árvore de módulos verdadeiramente aninhada (ver design.md).

## Critérios de aceite

Ver `specs/features/06-suporte-gradle/requirements.md` — os critérios de aceite da feature já são inteiramente o escopo desta fatia (não há uma fatia posterior de leitura planejada).

## Definição de pronto

`uv run pytest` verde; `detect_adapter` reconhece um projeto Gradle (Groovy ou Kotlin) e devolve `GradleAdapter`; `infer_structure` produz uma árvore completa, navegável na TUI existente sem nenhuma mudança nos painéis; nenhuma regressão no `MavenAdapter` (refatoração de `detect_directory_structure` para um módulo compartilhado).
