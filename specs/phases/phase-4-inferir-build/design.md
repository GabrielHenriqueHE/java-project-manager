# Fase 4 — Inferir Diretórios Registrados no Build — Design

## Novo módulo compartilhado: `src/manager/adapters/maven/build_helper.py`

Move as constantes hoje definidas em `writer.py` (usadas por `register_directory_role`) para um módulo que tanto `writer.py` (escrita) quanto `parser.py` (leitura) importam, evitando duas fontes de verdade para o mesmo mapeamento goal↔role:

```python
from manager.models import DirectoryRole

GROUP_ID = "org.codehaus.mojo"
ARTIFACT_ID = "build-helper-maven-plugin"
VERSION = "3.6.0"

ROLE_GOAL_PHASE: dict[DirectoryRole, tuple[str, str]] = {
    "source": ("add-source", "generate-sources"),
    "test-source": ("add-test-source", "generate-test-sources"),
    "resource": ("add-resource", "generate-resources"),
    "test-resource": ("add-test-resource", "generate-test-resources"),
}

GOAL_ROLE: dict[str, DirectoryRole] = {
    goal: role for role, (goal, _phase) in ROLE_GOAL_PHASE.items()
}
```

`writer.py` remove suas constantes locais (`BUILD_HELPER_GROUP_ID`, `BUILD_HELPER_ARTIFACT_ID`, `BUILD_HELPER_VERSION`, `_ROLE_GOAL_PHASE`) e importa de `build_helper.py` no lugar — comportamento idêntico, só elimina a duplicação; nenhum teste existente de `register_directory_role` muda.

## `MavenPomParser` (`src/manager/adapters/maven/parser.py`)

`ParsedPom` ganha:

```python
registered_directories: list[tuple[str, DirectoryRole]] = field(default_factory=list)
```

Em `parse()`, depois de montar `module_names`:

```python
registered_directories = self._parse_registered_directories(
    root.find(f"{ns}build"), ns
)
```

Novos métodos privados:

```python
def _parse_registered_directories(
    self, build_el: etree._Element | None, ns: str
) -> list[tuple[str, DirectoryRole]]:
    if build_el is None:
        return []
    plugins_el = build_el.find(f"{ns}plugins")
    if plugins_el is None:
        return []

    registered: list[tuple[str, DirectoryRole]] = []
    for plugin_el in plugins_el.findall(f"{ns}plugin"):
        if not self._is_build_helper_plugin(plugin_el, ns):
            continue
        executions_el = plugin_el.find(f"{ns}executions")
        if executions_el is None:
            continue
        for execution_el in executions_el.findall(f"{ns}execution"):
            registered.extend(self._parse_execution(execution_el, ns))
    return registered

@staticmethod
def _is_build_helper_plugin(plugin_el: etree._Element, ns: str) -> bool:
    group_id = MavenPomParser._text(plugin_el, "groupId", ns)
    artifact_id = MavenPomParser._text(plugin_el, "artifactId", ns)
    return group_id == build_helper.GROUP_ID and artifact_id == build_helper.ARTIFACT_ID

def _parse_execution(
    self, execution_el: etree._Element, ns: str
) -> list[tuple[str, DirectoryRole]]:
    goals_el = execution_el.find(f"{ns}goals")
    if goals_el is None:
        return []
    goal_el = goals_el.find(f"{ns}goal")
    goal = goal_el.text.strip() if goal_el is not None and goal_el.text else None
    role = build_helper.GOAL_ROLE.get(goal) if goal else None
    if role is None:
        return []

    config_el = execution_el.find(f"{ns}configuration")
    if config_el is None:
        return []

    if role in ("source", "test-source"):
        container_el, leaf_tag = config_el.find(f"{ns}sources"), "source"
        if container_el is None:
            return []
        return [
            (el.text.strip(), role)
            for el in container_el.findall(f"{ns}{leaf_tag}")
            if el.text
        ]

    resources_el = config_el.find(f"{ns}resources")
    if resources_el is None:
        return []
    paths = []
    for resource_el in resources_el.findall(f"{ns}resource"):
        dir_el = resource_el.find(f"{ns}directory")
        if dir_el is not None and dir_el.text:
            paths.append(dir_el.text.strip())
    return [(path, role) for path in paths]
```

Reaproveita `_text` (já existe no parser) para `groupId`/`artifactId`. Percorre `<plugin>`/`<execution>` em ordem de documento — determinístico, mesma ordem em que `register_directory_role` escreveu.

## `directory.py` — mescla no modelo de domínio

Novo helper, ao lado de `detect_directory_structure`:

```python
_ROLE_LIST_ATTR: dict[DirectoryRole, str] = {
    "source": "source_dirs",
    "test-source": "test_dirs",
    "resource": "resource_dirs",
    "test-resource": "test_resource_dirs",
}


def merge_registered_directories(
    structure: DirectoryStructure,
    module_dir: Path,
    registered: list[tuple[str, DirectoryRole]],
) -> DirectoryStructure:
    """Inclui diretorios registrados via build-helper-maven-plugin nas listas
    por role, se ainda existirem em disco. Nao mexe em `convention`/`tree`."""
    for relative_path, role in registered:
        if not (module_dir / relative_path).is_dir():
            continue
        attr = _ROLE_LIST_ATTR[role]
        current: list[str] = getattr(structure, attr)
        if relative_path not in current:
            setattr(structure, attr, [*current, relative_path])
    return structure
```

`role` aqui só assume os 4 valores de `_ROLE_LIST_ATTR` (garantido por `build_helper.GOAL_ROLE`, que nunca mapeia para `"other"`), então o `dict` cobre todos os casos sem `else`.

## `MavenAdapter._build_module`

```python
parsed = self._parser.parse(pom_path)
module_dir = pom_path.parent
...
directory_structure = detect_directory_structure(module_dir)
merge_registered_directories(
    directory_structure, module_dir, parsed.registered_directories
)
```

`merge_registered_directories` muta `directory_structure` in-place (Pydantic model comum, não congelado) e também retorna — chamada como statement, valor de retorno ignorado (mesmo padrão de `mkdir`/outras chamadas de efeito colateral no adapter).

## Casos de borda tratados

- `<build>` ausente, `<build><plugins>` ausente, plugin errado, ou `<execution>` com `goal` desconhecido: `registered_directories` fica vazio/parcial, sem erro — inferência nunca falha por causa de configuração de build que ela não reconhece.
- Diretório registrado no pom mas apagado do disco manualmente: filtrado por `is_dir()` no merge, igual à regra já usada por `detect_directory_structure` para os 4 diretórios convencionais.
- Mesmo diretório aparecendo tanto pela convenção padrão quanto por uma `<execution>` redundante (pom editado à mão): `if relative_path not in current` evita entrada duplicada na lista.
- Múltiplos `<source>`/`<resource>` na mesma `<execution>` (pom editado manualmente; a própria ferramenta nunca escreve mais de um): todos lidos e mesclados.
