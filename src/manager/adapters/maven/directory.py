from pathlib import Path

from manager.adapters.common.directory import STANDARD_DIRS, detect_directory_structure
from manager.models import DirectoryRole, DirectoryStructure

__all__ = [
    "STANDARD_DIRS",
    "detect_directory_structure",
    "merge_registered_directories",
]

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
