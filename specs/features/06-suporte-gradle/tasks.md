# Feature 06 — Suporte a Gradle — Tasks

**Fundação (leitura) implementada** na Fase 15 (`specs/phases/phase-15-gradle-fundacao/`): `GradleAdapter.detect`/`infer_structure`, Groovy e Kotlin DSL, árvore de módulos + group/version + dependências (diretas e gerenciadas via `java-platform`/`constraints{}` ou `platform(...)` externo) extraídos por um parser baseado em regex + contagem de chaves (subconjunto convencional da linguagem). Registrado em `services/adapters_registry.py`; nenhuma mudança na TUI foi necessária.

Ainda fora de escopo: todas as mutações (`add_module`, `update_dependency`, etc. — stubs `NotImplementedError`); version catalogs; `allprojects{}`/`subprojects{}`; `sourceSets{}` customizado; árvore de módulos verdadeiramente aninhada (hoje achatada sob a raiz).
