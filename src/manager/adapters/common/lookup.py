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
