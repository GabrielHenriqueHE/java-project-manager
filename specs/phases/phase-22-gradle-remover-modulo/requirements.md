# Fase 22 — Gradle: Remover Módulo — Requirements

Oitava fatia de [[06-suporte-gradle]]: `GradleAdapter.remove_module`.

## Escopo desta fatia

**Dentro:**
- `GradleWriter.remove_include(path, artifact_id) -> bool`: remove a entrada de `include(...)` (inverso de `add_include`, Fase 21); remove a declaração inteira se for a única entrada.
- `GradleAdapter.remove_module(project, module_name, *, force=False)`: espelha `MavenAdapter.remove_module` — conflito de dependentes, remoção da entrada gerenciada no BOM (se houver e não for o próprio módulo removido), remoção da dependência direta em cada dependente (quando `force=True` ignora o conflito).
- **Correção de bug**: `_FULL_DEP_LINE_RE` (Fase 18) tinha um `\s*` na cauda que atravessava quebras de linha e "engolia" a linha da dependência seguinte inteira quando um bloco (`constraints{}` ou `dependencies{}`) tinha mais de uma entrada — o bug só não tinha aparecido antes porque toda busca até aqui (`upsert`/`remove` das Fases 18-20) sempre encontrava a entrada certa na primeira ou única linha relevante do próprio teste. Corrigido trocando os `\s*` da cauda por `[ \t]*` (só espaço/tab na mesma linha).

**Fora:** nada — encerra as mutações de módulo desta feature.

## Critérios de aceite

- Dado um módulo sem dependentes, `remove_module` o remove da árvore (numa reinferência) e da declaração `include(...)`, sem apagar o diretório em disco.
- Dado um módulo com dependentes e `force=False`, levanta `DependentModuleConflict` com `module_name`/`dependents` corretos.
- Dado `force=True`, remove a entrada gerenciada no BOM (se o módulo removido tiver uma) e a dependência direta em cada módulo dependente.
- Remover o módulo raiz levanta `ValueError`.
- Um bloco de dependência com **duas ou mais** entradas continua funcionando corretamente em todas as mutações de dependência (upsert, remoção gerenciada, remoção direta) — cobertura de regressão para o bug do `_FULL_DEP_LINE_RE`.

## Definição de pronto

`uv run pytest` verde; `test_gradle_adapter_stubs.py` sem o caso de `remove_module` (só sobram `register_directory_role`/`unregister_directory_role`, permanentemente fora de escopo).
