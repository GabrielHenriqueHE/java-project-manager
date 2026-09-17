# Fase 9 — Marcar Diretório Registrado no Build — Design

## Abordagem

`DirectoryStructure` (Pydantic, `src/manager/models.py`) já usa `default_factory` para expressar o único caminho de convenção padrão por role: `source_dirs=["src/main/java"]`, `test_dirs=["src/test/java"]`, `resource_dirs=["src/main/resources"]`, `test_resource_dirs=["src/test/resources"]`. Qualquer outro valor presente numa dessas listas só entra ali via `merge_registered_directories` (`phase-4-inferir-build`), isto é, foi registrado explicitamente no build. Não é necessário nenhum campo novo no modelo de domínio nem acoplamento a `manager.adapters.maven`: basta comparar, dentro do próprio `structure_panel.py`, cada entrada de cada lista contra o único default esperado daquela lista.

Sem mudança de modelo de domínio, sem mudança de adapter — puramente apresentação (`structure_panel.py`).

## Implementação

`src/manager/screens/widgets/structure_panel.py`:

- Novo dict local `_STANDARD_BY_LIST = {"source_dirs": "src/main/java", "test_dirs": "src/test/java", "resource_dirs": "src/main/resources", "test_resource_dirs": "src/test/resources"}`.
- `_build_module_node` passa a iterar cada lista nomeada separadamente (em vez do `[*source_dirs, *resource_dirs, *test_dirs, *test_resource_dirs]` único atual), para saber a qual lista/role cada `rel` pertence e comparar com `_STANDARD_BY_LIST`.
- Quando `rel != _STANDARD_BY_LIST[list_name]`, o `_TreeNode` do diretório ganha o sufixo `"  [dim](build)[/]"` no texto — mesmo padrão visual já usado por `ModulesPanel` (`[dim]{packaging}[/]`) e `MetadataPanel`.
- `render_project_tree`/`_render_tree` não mudam de assinatura.

## Casos de borda

- Diretório com o mesmo nome relativo em duas roles diferentes não ocorre na prática (roles têm prefixos `src/main`/`src/test` distintos), não é tratado como caso especial.
- Diretório de convenção padrão ausente do disco já é filtrado antes (checagem `abs_dir.is_dir()` existente) — não muda.

## Alternativas descartadas

- Importar `STANDARD_DIRS` de `manager.adapters.maven.directory` — descartado por acoplar a camada de apresentação (que deveria ser agnóstica de build tool, decisão #3 do overview) a um adapter concreto; os defaults do próprio `DirectoryStructure` já bastam e são, por construção, os mesmos valores.
- Novo campo `DirectoryStructure.registered_dirs: list[str]` separado — descartado por ser mudança de modelo de domínio para uma necessidade puramente de apresentação; o dado já é derivável sem persistir estado extra.
