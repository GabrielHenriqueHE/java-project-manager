from pathlib import Path

from manager.models import (
    BuildFile,
    DirectoryStructure,
    Module,
    Project,
    ProjectMetadata,
)
from manager.screens.widgets.structure_panel import render_project_tree


def _make_project(root_path: Path, directory_structure: DirectoryStructure) -> Project:
    root_module = Module(
        name="core",
        relative_path=Path("."),
        metadata=ProjectMetadata(artifact_id="core", group_id="g", version="1.0"),
        directory_structure=directory_structure,
        build_file=BuildFile(path=Path("pom.xml")),
    )
    return Project(
        name="core",
        build_tool="maven",
        root_path=root_path,
        root_module=root_module,
    )


def test_standard_directory_has_no_build_marker(tmp_path):
    (tmp_path / "src/main/java").mkdir(parents=True)
    project = _make_project(
        tmp_path, DirectoryStructure(resource_dirs=[], test_dirs=[], test_resource_dirs=[])
    )

    tree = render_project_tree(project)

    assert "src/main/java/" in tree
    assert "(build)" not in tree


def test_registered_directory_outside_convention_is_marked(tmp_path):
    (tmp_path / "src/main/java").mkdir(parents=True)
    (tmp_path / "src/main/proto").mkdir(parents=True)
    structure = DirectoryStructure(
        source_dirs=["src/main/java", "src/main/proto"],
        resource_dirs=[],
        test_dirs=[],
        test_resource_dirs=[],
    )
    project = _make_project(tmp_path, structure)

    tree = render_project_tree(project)

    lines = tree.splitlines()
    java_line = next(line for line in lines if "src/main/java/" in line)
    proto_line = next(line for line in lines if "src/main/proto/" in line)

    assert "(build)" not in java_line
    assert "(build)" in proto_line


def test_registered_test_resource_directory_is_marked(tmp_path):
    (tmp_path / "src/test/resources").mkdir(parents=True)
    (tmp_path / "src/it/resources").mkdir(parents=True)
    structure = DirectoryStructure(
        source_dirs=[],
        resource_dirs=[],
        test_dirs=[],
        test_resource_dirs=["src/test/resources", "src/it/resources"],
    )
    project = _make_project(tmp_path, structure)

    tree = render_project_tree(project)

    lines = tree.splitlines()
    standard_line = next(line for line in lines if "src/test/resources/" in line)
    custom_line = next(line for line in lines if "src/it/resources/" in line)

    assert "(build)" not in standard_line
    assert "(build)" in custom_line
