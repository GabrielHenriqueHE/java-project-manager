from pathlib import Path

from manager.models import DirectoryNode, DirectoryStructure

STANDARD_DIRS = {
    "source": "src/main/java",
    "test-source": "src/test/java",
    "resource": "src/main/resources",
    "test-resource": "src/test/resources",
}


def detect_directory_structure(module_dir: Path) -> DirectoryStructure:
    """Infere a estrutura de diretorios de um modulo a partir do disco,
    usando a convencao-padrao de projeto Java (`src/main/java` etc.) -
    identica entre Maven e Gradle (o plugin `java`/`java-library` do
    Gradle usa exatamente o mesmo layout default do Maven).
    """
    src_dir = module_dir / "src"
    if not src_dir.is_dir():
        return DirectoryStructure(
            source_dirs=[], test_dirs=[], resource_dirs=[], test_resource_dirs=[]
        )

    present = {role: (module_dir / rel).is_dir() for role, rel in STANDARD_DIRS.items()}
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
            tree=build_tree(src_dir),
        )

    return DirectoryStructure(
        convention="maven-standard",
        source_dirs=[STANDARD_DIRS["source"]] if present["source"] else [],
        test_dirs=[STANDARD_DIRS["test-source"]] if present["test-source"] else [],
        resource_dirs=([STANDARD_DIRS["resource"]] if present["resource"] else []),
        test_resource_dirs=(
            [STANDARD_DIRS["test-resource"]] if present["test-resource"] else []
        ),
    )


def build_tree(path: Path) -> DirectoryNode:
    children = [build_tree(child) for child in sorted(path.iterdir()) if child.is_dir()]
    return DirectoryNode(name=path.name, children=children)
