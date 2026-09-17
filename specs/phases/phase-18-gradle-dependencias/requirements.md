# Fase 18 — Gradle: Dependências — Requirements

Quarta fatia de [[06-suporte-gradle]]: `GradleAdapter.update_dependency`.

## Escopo desta fatia

**Dentro:**
- `GradleWriter.upsert_dependency(path, dependency)`: adiciona ou atualiza (upsert por `group_id:artifact_id`) uma dependência gerenciada (dentro de `constraints{}`, sempre config `api`, cria `constraints{}`/`dependencies{}` se não existirem) ou direta (fora de `constraints{}`, config escolhido a partir de `dependency.scope`).
- `GradleAdapter.update_dependency`: mesmas validações do Maven (módulo existe; `group_id`/`artifact_id` obrigatórios; gerenciada exige `packaging="pom"` e `version`), mais o guard de "módulo sem `build.gradle(.kts)`" já introduzido na Fase 17.

**Fora (fatias futuras):**
- `remove_dependency`/`remove_direct_dependency` (Fases 19/20).

## Critérios de aceite

- Dado um módulo `packaging="pom"`, quando `update_dependency` recebe uma dependência gerenciada nova, então ela aparece em `constraints{}` (criando o bloco se preciso) e é lida de volta por `infer_structure` como `managed=True`.
- Dado uma dependência gerenciada já existente (mesmo `group_id:artifact_id`), quando `update_dependency` é chamado de novo com uma `version` diferente, então a linha existente é substituída no lugar (sem duplicar).
- Dado uma dependência direta nova, quando `update_dependency` é chamado, então ela aparece fora de `constraints{}`, com o config escolhido a partir de `dependency.scope` (`compile`/`None`→`implementation`, `provided`→`compileOnly`, `runtime`→`runtimeOnly`, `test`→`testImplementation`, qualquer outro valor→`implementation`).
- Dado um módulo sem `dependencies{}` no arquivo, quando `update_dependency` é chamado, então o bloco é criado do zero.
- Mesmas rejeições do Maven: `group_id`/`artifact_id` ausentes, gerenciada sem `version`, gerenciada em módulo não-`pom`, módulo inexistente.

## Definição de pronto

`uv run pytest` verde; `test_gradle_adapter_stubs.py` sem o caso de `update_dependency`.
