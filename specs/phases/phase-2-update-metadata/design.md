# Fase 2 — Atualizar Metadados — Design

## `xml_utils.ensure_child_in_order`

Novo helper genérico (usado por `update_metadata` e reaproveitável por `update_dependency` para `dependencyManagement`/`dependencies`): dado um `container`, uma `tag` e a lista de tags do elemento pai na ordem canônica do XSD do POM (`_POM_ELEMENT_ORDER`), retorna o elemento filho existente com essa tag ou cria um novo, inserindo-o na posição correta (antes do primeiro filho existente cuja tag venha depois na ordem canônica; se nenhum, `append` no fim), reproduzindo indentação via `append_with_matching_indent`/lógica equivalente adaptada para `insert`.

```python
_POM_ELEMENT_ORDER = [
    "modelVersion", "parent", "groupId", "artifactId", "version", "packaging",
    "name", "description", "properties", "dependencyManagement", "dependencies",
    "modules", "build",
]

def ensure_child_in_order(container, tag, ns, order=_POM_ELEMENT_ORDER) -> etree._Element:
    existing = container.find(f"{ns}{tag}")
    if existing is not None:
        return existing
    new_el = etree.Element(f"{ns}{tag}")
    target_idx = order.index(tag)
    for sibling in container:
        sibling_tag = etree.QName(sibling).localname
        if sibling_tag in order and order.index(sibling_tag) > target_idx:
            sibling.addprevious(new_el)
            # indentacao: copia o padrao de texto/tail dos vizinhos existentes
            ...
            return new_el
    container.append(new_el)
    ...
    return new_el
```

Detalhe de indentação: como os elementos de topo do pom (filhos de `<project>`) usam `container.text`/`tail` de cada filho para indentação (mesmo padrão de `append_with_matching_indent`), a inserção reaproveita o `tail` do elemento anterior (ou `container.text` se for o primeiro filho) como `text` de separação, e usa esse mesmo padrão como `tail` do novo elemento — garantindo que o elemento seguinte não perca sua indentação.

## `MavenPomWriter`

- `set_or_remove_scalar(pom_path, tag, value, *, ns, order)` — helper interno: se `value` truthy, `ensure_child_in_order(root, tag, ns).text = value`; se `value` é `None`/vazio, remove a tag (se existir) via `remove_element_preserving_whitespace`. Usado para `name`, `description`, `groupId`, `version`.
- `update_metadata(pom_path, metadata: ProjectMetadata, *, has_parent: bool) -> None` — orquestra as escritas pontuais num único parse/write (evita reabrir o arquivo 5x):
  1. `groupId`: escreve se `metadata.group_id` truthy, senão remove (idempotente se já ausente).
  2. `version`: idem.
  3. `artifactId`: **não é tocado** — a chamada nunca recebe um `artifactId` diferente do módulo (validado antes, no adapter).
  4. `packaging`: sempre escreve o valor (`ensure_child_in_order` + set text) — campo obrigatório, sem noção de "remover".
  5. `name`/`description`: escreve se truthy, senão remove.
  6. `java_version`: se truthy, `ensure_child_in_order(root, "properties", ns)` e dentro dele `ensure_child_in_order(properties_el, "maven.compiler.source"/".target", ns)`, setando o texto; se `None`, remove as duas properties (se existirem) e remove `<properties>` se ficar vazio (mesma lógica de limpeza de container vazio já usada em `remove_managed_dependency`).
  7. Um único `self._write(tree, pom_path)` ao final.

## `MavenAdapter.update_metadata`

Fluxo (`src/manager/adapters/maven/adapter.py`):

1. `_find_module(root_module, module_name)` — `ValueError` se não encontrado (reaproveitado).
2. Valida `metadata.artifact_id == target.metadata.artifact_id` — senão `ValueError` ("renomear artifactId nao suportado"), mesma proteção que a TUI já aplica ao tornar o campo somente-leitura.
3. Valida `packaging`: se `metadata.packaging != target.metadata.packaging` e (`target.submodules` não vazio ou `target.is_bom`) e `metadata.packaging != "pom"` → `ValueError` ("modulo com submodulos/BOM precisa manter packaging=pom").
4. Resolve herança de `groupId`/`version`: busca o pai via `_find_parent(root_module, target)` (reaproveitado de `remove_module`).
   - Se `parent is None` (é a raiz): `metadata.group_id`/`metadata.version` **obrigatórios** (`ValueError` se vazios).
   - Se `parent` existe: se `metadata.group_id == parent.metadata.group_id`, passa `None` ao writer (herança implícita); mesma regra para `version`. Caso contrário passa o valor explícito.
5. Resolve `java_version`: extrai de `metadata.properties.get("maven.compiler.source")` (o form já monta o dict assim — ver seção TUI) e passa ao writer.
6. Chama `writer.update_metadata(pom_path, ..., has_parent=parent is not None)`.
7. Retorna `self.infer_structure(root_path)`.

`pom_path = root_path / target.build_file.path`.

## TUI

- `MetadataFormScreen` (`src/manager/screens/widgets/metadata_form.py`, novo): `ModalScreen[ProjectMetadata | None]`, mesmo padrão visual do `ModuleFormScreen`. Recebe o `Module` atual no construtor e pré-preenche os campos (`name`, `groupId`, `version`, `java.version` via `properties.get("maven.compiler.source", "")`, `packaging`, `description`); `artifactId` é mostrado como `Static` (rótulo), não `Input`. Confirmar monta um `ProjectMetadata` (com `properties={"maven.compiler.source": java_version, "maven.compiler.target": java_version}` se `java_version` informado, senão `{}`) e usa `artifact_id=module.metadata.artifact_id` (sempre o original, nunca editável) e `dismiss(metadata)`; cancelar `dismiss(None)`.
- `MetadataPanel.action_edit` (`src/manager/screens/widgets/metadata_panel.py:54`) passa a chamar `self.screen.update_metadata(self._module)` ao invés de mostrar o aviso "nao implementada" — segue o padrão já usado por `ModulesPanel`/`ProjectsPanel` de delegar ações para `MainScreen` via `self.screen`. `MetadataPanel` precisa passar a guardar `self._module` (hoje só usa o parâmetro local de `refresh_module`, sem guardar estado).
- `MainScreen.update_metadata(module: Module) -> None` (novo, mesmo padrão de `add_module`/`remove_module`): abre `MetadataFormScreen(module)`; no callback, se `metadata is not None`, chama `self._adapter.update_metadata(self.project, module.name, metadata)`, trata `ValueError` via `self.notify(..., severity="error")`, e em sucesso `self.notify("Metadados atualizados")` + `self.set_project(updated)`.

## Casos de borda tratados

- Módulo raiz sem `groupId`/`version` informado: erro claro, nenhuma escrita.
- `groupId`/`version` igual ao do pai: tag explícita removida/omitida (herança implícita), mesmo se já existisse explícita no pom antes da edição.
- `java_version` limpo quando `<properties>` tem outras entradas além de `maven.compiler.source/target`: só as duas properties de Java são removidas, `<properties>` permanece com as demais.
- Tentativa de mudar `packaging` de um módulo BOM ou com submódulos: barrada antes de qualquer escrita.
- Tentativa de mudar `artifactId` via chamada direta ao adapter (bypass da TUI): barrada com o mesmo erro claro.
- Inserir `<description>` num pom que nunca teve essa tag: `ensure_child_in_order` insere na posição correta (depois de `<name>`, antes de `<properties>`), preservando validade do XSD.
