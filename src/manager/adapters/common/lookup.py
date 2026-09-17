from pathlib import Path

from manager.models import Module, Project


def find_module(module: Module, name: str) -> Module | None:
    """Busca em profundidade por um modulo com o nome informado, na arvore
    a partir de `module` (inclusive). Identico entre build tools - opera
    apenas sobre a arvore de dominio agnostica.
    """
    if module.name == name:
        return module
    for sub in module.submodules:
        found = find_module(sub, name)
        if found is not None:
            return found
    return None


def find_parent(module: Module, target: Module) -> Module | None:
    """Busca o modulo pai direto de `target` na arvore a partir de `module`.

    Identifica `target` por `relative_path` (nao por identidade de objeto),
    entao funciona sobre uma copia recem-inferida da mesma arvore. Retorna
    None se `target` for a propria raiz (sem pai) ou nao for encontrado.
    """
    for sub in module.submodules:
        if sub.relative_path == target.relative_path:
            return module
        found = find_parent(sub, target)
        if found is not None:
            return found
    return None


def find_bom_module(module: Module) -> Module | None:
    """Busca em profundidade o primeiro modulo com `is_bom=True`."""
    if module.is_bom:
        return module
    for sub in module.submodules:
        found = find_bom_module(sub)
        if found is not None:
            return found
    return None


def find_dependents(root_module: Module, target: Module) -> list[Module]:
    """Lista os modulos que declaram uma dependencia DIRETA (managed=False)
    em `target`, identificado por (group_id, artifact_id). Nao considera
    o proprio `target` (comparado por `relative_path`).
    """
    target_key = (target.metadata.group_id, target.metadata.artifact_id)
    dependents: list[Module] = []

    def walk(module: Module) -> None:
        if module.relative_path != target.relative_path:
            for dep in module.dependencies:
                if not dep.managed and (dep.group_id, dep.artifact_id) == target_key:
                    dependents.append(module)
                    break
        for sub in module.submodules:
            walk(sub)

    walk(root_module)
    return dependents


def find_managed_dependency_owner(
    module: Module, group_id: str, artifact_id: str
) -> Module | None:
    """Busca em profundidade o modulo que declara (group_id, artifact_id)
    como dependencia gerenciada (managed=True) entre suas `dependencies`.
    """
    for dep in module.dependencies:
        if dep.managed and dep.group_id == group_id and dep.artifact_id == artifact_id:
            return module
    for sub in module.submodules:
        found = find_managed_dependency_owner(sub, group_id, artifact_id)
        if found is not None:
            return found
    return None


def resolve_module_relative_path(
    project: Project, target: Module, relative_path: Path
) -> Path:
    """Resolve `relative_path` contra o diretorio de `target`, levantando
    ValueError se o resultado escapar do diretorio do modulo.
    """
    module_dir = (project.root_path / target.relative_path).resolve()
    target_path = (module_dir / relative_path).resolve()
    if module_dir not in (target_path, *target_path.parents):
        raise ValueError(
            f"'{relative_path}' escapa do diretorio do modulo '{target.name}'"
        )
    return target_path
