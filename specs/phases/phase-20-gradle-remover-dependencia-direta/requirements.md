# Fase 20 — Gradle: Remover Dependência Direta — Requirements

Sexta fatia de [[06-suporte-gradle]]: `GradleAdapter.remove_direct_dependency`.

## Escopo desta fatia

**Dentro:**
- `GradleWriter.remove_dependency(path, group_id, artifact_id) -> bool`: remove uma entrada direta (fora de `constraints{}`) de `dependencies{}`, colapsando o bloco inteiro se ficar vazio. Nome espelha o par `remove_managed_dependency`/`remove_dependency` do `MavenPomWriter`.
- `GradleAdapter.remove_direct_dependency(project, module_name, group_id, artifact_id)`: módulo é sempre explícito (uma dependência direta pertence a um único `build.gradle`), mesma assinatura do Maven.

**Fora:** nada — encerra as mutações de dependência desta feature (`update_dependency`, `remove_dependency`, `remove_direct_dependency` cobrem os três casos previstos).

## Critérios de aceite

- Dado uma dependência direta existente, quando removida, então some de `Module.dependencies` numa reinferência e a linha desaparece do arquivo.
- Removendo a última dependência direta (e nenhuma gerenciada) de um módulo, o bloco `dependencies{}` inteiro desaparece.
- Uma dependência **gerenciada** com as mesmas coordenadas (dentro de `constraints{}`, em qualquer módulo) nunca é confundida com uma direta — buscar por ela via `remove_direct_dependency` no módulo que só a tem como gerenciada levanta `ValueError`.
- Dependência inexistente ou módulo inexistente levantam `ValueError`.

## Definição de pronto

`uv run pytest` verde; `test_gradle_adapter_stubs.py` sem o caso de `remove_direct_dependency`.
