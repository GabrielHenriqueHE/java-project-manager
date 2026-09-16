from pathlib import Path

from manager.models import DirectoryNode, DirectoryRole, DirectoryStructure

_STANDARD_DIRS = {
    "source": "src/main/java",
    "test-source": "src/test/java",
    "resource": "src/main/resources",
    "test-resource": "src/test/resources",
}

_ROLE_LIST_ATTR: dict[DirectoryRole, str] = {
    "source": "source_dirs",
    "test-source": "test_dirs",
    "resource": "resource_dirs",
    "test-resource": "test_resource_dirs",
}


def detect_directory_structure(module_dir: Path) -> DirectoryStructure:
    """Infere a estrutura de diretorios de um modulo Maven a partir do disco."""
    src_dir = module_dir / "src"
    if not src_dir.is_dir():
        return DirectoryStructure(
            source_dirs=[], test_dirs=[], resource_dirs=[], test_resource_dirs=[]
        )

    present = {
        role: (module_dir / rel).is_dir() for role, rel in _STANDARD_DIRS.items()
    }
    non_standard_entries = [
        child
        for child in src_dir.iterdir()
        if child.is_dir() and child.name not in {"main", "test"}
    ]

    if non_standard_entries or not any(present.values()):
        return DirectoryStructure(
            convention="custom",
            source_dirs=[],
            test_dirs=[],
            resource_dirs=[],
            test_resource_dirs=[],
            tree=_build_tree(src_dir),
        )

    return DirectoryStructure(
        convention="maven-standard",
        source_dirs=[_STANDARD_DIRS["source"]] if present["source"] else [],
        test_dirs=[_STANDARD_DIRS["test-source"]] if present["test-source"] else [],
        resource_dirs=([_STANDARD_DIRS["resource"]] if present["resource"] else []),
        test_resource_dirs=(
            [_STANDARD_DIRS["test-resource"]] if present["test-resource"] else []
        ),
    )


def merge_registered_directories(
    structure: DirectoryStructure,
    module_dir: Path,
    registered: list[tuple[str, DirectoryRole]],
) -> DirectoryStructure:
    """Inclui diretorios registrados via build-helper-maven-plugin (lidos de
    volta do <build><plugins> pelo parser) nas listas por role, se ainda
    existirem em disco. Nao mexe em `convention`/`tree`.
    """
    for relative_path, role in registered:
        if not (module_dir / relative_path).is_dir():
            continue
        attr = _ROLE_LIST_ATTR[role]
        current: list[str] = getattr(structure, attr)
        if relative_path not in current:
            setattr(structure, attr, [*current, relative_path])
    return structure


def _build_tree(path: Path) -> DirectoryNode:
    children = [
        _build_tree(child) for child in sorted(path.iterdir()) if child.is_dir()
    ]
    return DirectoryNode(name=path.name, children=children)
