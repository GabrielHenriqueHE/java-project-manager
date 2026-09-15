# Fase 2 — Atualizar Dependência — Design

## `MavenPomWriter`

- `_append_dependency_element` (já existente, usado por `create_pom`) ganha suporte a `type`/`classifier` (hoje só escreve `groupId`/`artifactId`/`version`/`scope`) — extensão aditiva: `Dependency` já tem esses campos no modelo, só não eram serializados. Isso beneficia também `create_pom`, sem alterar o comportamento para dependências que não usam esses campos (continuam omitidos quando `None`).
- `update_dependency(pom_path, module_name_dependency: Dependency) -> None`:
  1. `tree, root, ns = self._parse(pom_path)`.
  2. Resolve o container: se `dependency.managed`, `dep_mgmt_el = ensure_child_in_order(root, "dependencyManagement", ns)` e `deps_el = ensure_child_in_order(dep_mgmt_el, "dependencies", ns)`; senão `deps_el = ensure_child_in_order(root, "dependencies", ns)`.
  3. Busca uma `<dependency>` existente em `deps_el` cujo `(groupId, artifactId)` bate com `dependency` (reaproveita o padrão de busca já usado em `_remove_matching_dependency`, mas sem remover).
  4. Se encontrada: atualiza/remove in-place os filhos `version`/`scope`/`type`/`classifier` (mesmo padrão "set ou remove" de `update_metadata`, mas dentro do elemento `<dependency>`).
  5. Se não encontrada: cria um novo `<dependency>` via `_append_dependency_element` (agora com `type`/`classifier`) e anexa com `append_with_matching_indent(deps_el, new_el)`.
  6. `self._write(tree, pom_path)`.

`ensure_child_in_order` (de `phase-2-update-metadata`) é reaproveitado tanto para o elemento de topo (`dependencyManagement`/`dependencies` diretas) quanto, com uma ordem própria (`["groupId", "artifactId", "version", "type", "classifier", "scope"]`, ordem real do XSD `Dependency` do POM 4.0.0 — note que difere da ordem usada em `_append_dependency_element` hoje, que não inclui `type` antes de `scope`; ao estender esse helper, a ordem de escrita passa a seguir o XSD), aninhado dentro de `dependencyManagement`.

## `MavenAdapter.update_dependency`

Fluxo (`src/manager/adapters/maven/adapter.py`):

1. `_find_module(root_module, module_name)` — `ValueError` se não encontrado.
2. Valida `dependency.group_id`/`dependency.artifact_id` não vazios (guarda defensiva; o form da TUI já valida, mas a API do adapter é chamada também pelos testes).
3. Se `dependency.managed`:
   - Valida `target.metadata.packaging == "pom"` — senão `ValueError` ("modulo precisa ter packaging=pom para receber dependencia gerenciada").
   - Valida `dependency.version` presente — senão `ValueError` ("versao e obrigatoria para dependencia gerenciada").
4. Chama `writer.update_dependency(pom_path, dependency)`.
5. Retorna `self.infer_structure(root_path)`.

`pom_path = root_path / target.build_file.path`.

## TUI

- `DependencyFormScreen` (`src/manager/screens/widgets/dependency_form.py`, novo): `ModalScreen[Dependency | None]`, mesmo padrão visual de `ModuleFormScreen`/`MetadataFormScreen`. Campos: `groupId` (obrigatório), `artifactId` (obrigatório), `version` (obrigatório — o form é usado apenas para entradas gerenciadas nesta fatia), `scope` (opcional), `type` (opcional). Confirmar monta `Dependency(managed=True, ...)` e `dismiss(dependency)`; cancelar `dismiss(None)`.
- `BomPanel.action_add_dependency` (`src/manager/screens/widgets/bom_panel.py:84`) passa a chamar `self.screen.add_dependency()` em vez de mostrar o aviso "nao implementado".
- `MainScreen.add_dependency() -> None` (novo, mesmo padrão de `add_module`): resolve o módulo alvo (`self.selected_module or self.project.root_module`), abre `DependencyFormScreen`; no callback, se `dependency is not None`, chama `self._adapter.update_dependency(self.project, target_module.name, dependency)`, trata `ValueError` via `self.notify(..., severity="error")`, e em sucesso `self.notify(f"Dependencia '{dependency.artifact_id}' registrada")` + `self.set_project(updated)`.

## Casos de borda tratados

- Módulo alvo sem `<dependencyManagement>`/`<dependencies>` ainda: seções criadas na posição correta (via `ensure_child_in_order`).
- `groupId:artifactId` repetido: atualiza a entrada existente (version/scope/type/classifier), não duplica.
- Módulo alvo com `packaging != pom`: barrado antes de qualquer escrita.
- `version` ausente numa entrada gerenciada: barrado antes de qualquer escrita.
- Entrada existente perde um campo opcional (ex.: `scope` que existia é limpo no form): a tag correspondente é removida do `<dependency>` (mesmo padrão "set ou remove" de `update_metadata`).
