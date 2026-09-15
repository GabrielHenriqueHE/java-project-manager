# Fase 4 — Registrar Diretório no Build — Design

## `BuildToolAdapter.register_directory_role` (`src/manager/adapters/base.py`)

```python
@abstractmethod
def register_directory_role(
    self, project: Project, module_name: str, relative_path: Path, role: DirectoryRole
) -> Project:
    """Registra relative_path como fonte/recurso extra no arquivo de build.

    role precisa ser um de: source, test-source, resource, test-resource
    ('other' e invalido). Levanta ValueError se o modulo nao existir, se
    role for invalido, ou se o diretorio ainda nao existir em disco
    (precisa ser criado antes via add_directory).
    """
```

## `MavenPomWriter.register_directory_role`

Constantes novas (`src/manager/adapters/maven/writer.py`):

```python
BUILD_HELPER_GROUP_ID = "org.codehaus.mojo"
BUILD_HELPER_ARTIFACT_ID = "build-helper-maven-plugin"
BUILD_HELPER_VERSION = "3.6.0"

_ROLE_GOAL_PHASE = {
    "source": ("add-source", "generate-sources"),
    "test-source": ("add-test-source", "generate-test-sources"),
    "resource": ("add-resource", "generate-resources"),
    "test-resource": ("add-test-resource", "generate-test-resources"),
}
```

Fluxo de `register_directory_role(pom_path, relative_path, role)`:

1. `goal, phase = _ROLE_GOAL_PHASE[role]` (chamador — o adapter — já valida `role`; o writer confia nisso, mas o dict só tem essas 4 chaves então um `role` inválido levantaria `KeyError` se chegasse aqui, o que não deveria acontecer dado o contrato).
2. `execution_id = f"add-{role}-" + relative_path.replace("/", "-")` — determinístico, usado tanto para nomear a `<execution>` quanto para checar idempotência.
3. `tree, root, ns = self._parse(pom_path)`.
4. `build_el = ensure_child_in_order(root, "build", ns)`.
5. `plugins_el = ensure_child_in_order(build_el, "plugins", ns, order=["plugins"])` — `order` customizado de um elemento só, porque `POM_ELEMENT_ORDER` (de `xml_utils.py`) só ordena os filhos diretos de `<project>`, não os de `<build>`; como `<plugins>` normalmente é o único filho relevante de `<build>` que esta fatia mexe, um `next_sibling` não encontrado cai no fallback de `append_with_matching_indent` (mesmo comportamento de "append no fim", correto na prática: `<plugins>` já costuma vir por último dentro de `<build>`).
6. `plugin_el = self._find_plugin_element(plugins_el, ns, BUILD_HELPER_GROUP_ID, BUILD_HELPER_ARTIFACT_ID)` (novo helper, mesmo padrão de `_find_dependency_element`, comparando `groupId`/`artifactId`).
7. Se `plugin_el is None`: constrói um `<plugin>` desanexado (`groupId`, `artifactId`, `version=BUILD_HELPER_VERSION`), anexa via `append_with_matching_indent`, indenta com `etree.indent(plugin_el, space="  ", level=depth)` (mesma técnica de `_append_dependency_element`). Se já existir, **não toca em nada dele** (nem na `<version>` — ver riscos no requirements).
8. `executions_el = ensure_child_in_order(plugin_el, "executions", ns, order=["executions"])`.
9. Se `self._find_execution_element(executions_el, ns, execution_id)` já existe → `return` sem escrever (idempotente).
10. Constrói `<execution>` desanexado, com filhos `id`, `phase`, `goals><goal`, e `configuration` variando por `role`:
    - `source`/`test-source`: `configuration><sources><source>{relative_path}</source>`.
    - `resource`/`test-resource`: `configuration><resources><resource><directory>{relative_path}</directory>`.
11. `append_with_matching_indent(executions_el, execution_el)`; `etree.indent(execution_el, space="  ", level=depth_of(execution_el))` — um único `etree.indent` no elemento raiz da subárvore nova já formata todos os níveis aninhados (`id`/`phase`/`goals`/`goal`/`configuration`/`sources`/`source`), mesma garantia genérica de `etree.indent` usada em `_append_dependency_element`.
12. `self._write(tree, pom_path)`.

### Novos helpers privados

- `_find_plugin_element(plugins_el, ns, group_id, artifact_id)` — busca linear por `<plugin>` com `groupId`/`artifactId` batendo, mesmo padrão de `_find_dependency_element`.
- `_find_execution_element(executions_el, ns, execution_id)` — busca linear por `<execution>` com `<id>` batendo.

## `MavenAdapter.register_directory_role`

Fluxo (`src/manager/adapters/maven/adapter.py`):

1. `_find_module` — `ValueError` se não encontrado.
2. `ValueError` se `role not in {"source", "test-source", "resource", "test-resource"}` (mensagem clara, não deixa a validação vazar como `KeyError` do writer).
3. `target_path = self._resolve_module_relative_path(project, target, relative_path)` (reaproveitado de `add_directory`/`remove_directory`).
4. `ValueError` ("nao existe; crie o diretorio primeiro") se `not target_path.is_dir()`.
5. `pom_path = project.root_path / target.build_file.path`; `self._writer.register_directory_role(pom_path, str(relative_path), role)`.
6. Retorna `self.infer_structure(project.root_path)`.

## TUI

- `BuildSourceFormScreen` (`src/manager/screens/widgets/build_source_form.py`, novo): `ModalScreen[tuple[str, str] | None]`, dois campos — `#field-path` (caminho relativo) e `#field-role` (texto livre, mesmo padrão de `packaging` em `MetadataFormScreen`; placeholder lista os 4 valores aceitos). Confirmar valida ambos não-vazios e `role` num dos 4 valores (senão feedback no próprio form, nenhuma chamada ao adapter); `dismiss((path, role))`. Cancelar `dismiss(None)`.
- `StructurePanel` ganha `("b", "register_build_source", "build")`; `action_register_build_source` resolve módulo ativo e chama `self.screen.register_build_source(active_module)`.
- `MainScreen.register_build_source(module)`: abre `BuildSourceFormScreen`; no callback, chama `self._adapter.register_directory_role(self.project, module.name, Path(path), role)`; erro do adapter vira notificação (`severity="error"`); sucesso notifica e `set_project(updated)`.

## Casos de borda tratados

- `<build>`/`<plugins>` ausentes: criados na posição correta.
- Segunda pasta/role no mesmo módulo: reaproveita o `<plugin>` existente, só adiciona `<execution>`.
- Mesma pasta/role duas vezes: no-op, nenhuma escrita na segunda vez.
- Diretório inexistente: erro claro antes de qualquer escrita.
- `role` inválido (`other` ou qualquer string fora das 4): erro claro no adapter, validado também no formulário antes de chegar lá.
