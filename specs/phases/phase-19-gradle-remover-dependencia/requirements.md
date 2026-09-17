# Fase 19 — Gradle: Remover Dependência Gerenciada — Requirements

Quinta fatia de [[06-suporte-gradle]]: `GradleAdapter.remove_dependency`.

## Escopo desta fatia

**Dentro:**
- `GradleWriter.remove_managed_dependency(path, group_id, artifact_id) -> bool`: remove a linha correspondente de dentro de `constraints{}`; colapsa `constraints{}` inteiro se ficar vazio, e `dependencies{}` inteiro se também ficar vazio depois disso.
- `GradleAdapter.remove_dependency(project, group_id, artifact_id)`: localiza o módulo dono via `find_managed_dependency_owner` (extraído na Fase 17) em qualquer lugar da árvore, delega ao writer.

**Fora:** `remove_direct_dependency` (Fase 20).

## Critérios de aceite

- Dado uma dependência gerenciada existente, quando `remove_dependency` é chamado, então ela some de `constraints{}` e de `Project.managed_dependencies` numa reinferência.
- Dado a última entrada de `constraints{}`, quando removida, então o bloco `constraints{}` inteiro desaparece do arquivo; se `dependencies{}` também ficar sem mais nada, ele também desaparece.
- Dado uma dependência gerenciada inexistente, então levanta `ValueError`.
- Remover uma entrada gerenciada não deve afetar uma dependência **direta** com as mesmas coordenadas em outro módulo (ex.: `api` depende diretamente de `com.example:core`, `bom` a gerencia — remover a gerenciada não deve tocar a direta).

## Definição de pronto

`uv run pytest` verde; `test_gradle_adapter_stubs.py` sem o caso de `remove_dependency`.
