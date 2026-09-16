import shutil
from pathlib import Path

import pytest

from manager.adapters.maven.adapter import MavenAdapter
from manager.manifest import (
    ModuleManifest,
    dump_manifest,
    export_source_files,
    is_bom_manifest,
    load_manifest,
    to_manifest,
    validate_manifest_tree,
)
from manager.models import (
    BuildFile,
    Dependency,
    DirectoryNode,
    DirectoryStructure,
    Module,
    ProjectMetadata,
)

FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "maven-multi-module"


def test_load_manifest_parses_yaml(tmp_path):
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text("""
metadata:
  artifact_id: demo
  group_id: com.example
  version: "1.0.0"
  packaging: pom
submodules:
  - metadata:
      artifact_id: core
""")

    manifest = load_manifest(manifest_path)

    assert manifest.metadata.artifact_id == "demo"
    assert manifest.metadata.packaging == "pom"
    assert len(manifest.submodules) == 1
    assert manifest.submodules[0].metadata.artifact_id == "core"


def test_validate_manifest_tree_accepts_unique_names():
    manifest = ModuleManifest(
        metadata=ProjectMetadata(artifact_id="demo", packaging="pom"),
        submodules=[
            ModuleManifest(metadata=ProjectMetadata(artifact_id="core")),
            ModuleManifest(metadata=ProjectMetadata(artifact_id="api")),
        ],
    )

    validate_manifest_tree(manifest)  # nao levanta


def test_validate_manifest_tree_rejects_duplicate_names():
    manifest = ModuleManifest(
        metadata=ProjectMetadata(artifact_id="demo", packaging="pom"),
        submodules=[
            ModuleManifest(metadata=ProjectMetadata(artifact_id="core")),
            ModuleManifest(metadata=ProjectMetadata(artifact_id="core")),
        ],
    )

    with pytest.raises(ValueError, match="duplicado"):
        validate_manifest_tree(manifest)


def test_is_bom_manifest_requires_pom_and_managed_dependency():
    bom = ModuleManifest(
        metadata=ProjectMetadata(artifact_id="bom", packaging="pom"),
        dependencies=[
            Dependency(
                group_id="org.apache.commons",
                artifact_id="commons-lang3",
                version="3.14.0",
                managed=True,
            )
        ],
    )
    not_bom_wrong_packaging = ModuleManifest(
        metadata=ProjectMetadata(artifact_id="core", packaging="jar"),
        dependencies=[
            Dependency(
                group_id="org.apache.commons",
                artifact_id="commons-lang3",
                version="3.14.0",
                managed=True,
            )
        ],
    )
    not_bom_no_managed_deps = ModuleManifest(
        metadata=ProjectMetadata(artifact_id="parent", packaging="pom"),
    )

    assert is_bom_manifest(bom) is True
    assert is_bom_manifest(not_bom_wrong_packaging) is False
    assert is_bom_manifest(not_bom_no_managed_deps) is False


def test_to_manifest_drops_disk_only_fields_and_tree():
    module = Module(
        name="core",
        relative_path=Path("core"),
        metadata=ProjectMetadata(
            artifact_id="core", group_id="com.example", version="1.0.0"
        ),
        dependencies=[
            Dependency(
                group_id="org.apache.commons",
                artifact_id="commons-lang3",
                version="3.14.0",
            )
        ],
        directory_structure=DirectoryStructure(
            source_dirs=["src/main/java"],
            test_dirs=[],
            resource_dirs=[],
            test_resource_dirs=[],
            tree=DirectoryNode(name="src"),
        ),
        build_file=BuildFile(path=Path("core/pom.xml")),
    )

    manifest = to_manifest(module)

    assert manifest.metadata.artifact_id == "core"
    assert manifest.dependencies[0].artifact_id == "commons-lang3"
    assert manifest.directory_structure.tree is None
    assert manifest.directory_structure.source_dirs == ["src/main/java"]
    assert not hasattr(manifest, "relative_path")
    assert not hasattr(manifest, "build_file")


def test_to_manifest_recurses_into_submodules():
    child = Module(
        name="api",
        relative_path=Path("api"),
        metadata=ProjectMetadata(artifact_id="api"),
        build_file=BuildFile(path=Path("api/pom.xml")),
    )
    parent = Module(
        name="demo",
        relative_path=Path("."),
        metadata=ProjectMetadata(
            artifact_id="demo",
            group_id="com.example",
            version="1.0.0",
            packaging="pom",
        ),
        build_file=BuildFile(path=Path("pom.xml")),
        submodules=[child],
    )

    manifest = to_manifest(parent)

    assert len(manifest.submodules) == 1
    assert manifest.submodules[0].metadata.artifact_id == "api"


def test_dump_manifest_then_load_manifest_roundtrips(tmp_path):
    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo", group_id="com.example", version="1.0.0"
        ),
    )
    path = tmp_path / "manifest.yaml"

    dump_manifest(manifest, path)
    loaded = load_manifest(path)

    assert loaded == manifest


def test_dump_manifest_overwrites_existing_file(tmp_path):
    path = tmp_path / "manifest.yaml"
    path.write_text("conteudo antigo")
    manifest = ModuleManifest(metadata=ProjectMetadata(artifact_id="demo"))

    dump_manifest(manifest, path)

    assert "conteudo antigo" not in path.read_text()


@pytest.fixture
def project_root(tmp_path) -> Path:
    dest = tmp_path / "project"
    shutil.copytree(FIXTURE_SOURCE, dest)
    return dest


def test_export_source_files_copies_only_matching_modules(project_root, tmp_path):
    project = MavenAdapter().infer_structure(project_root)
    manifest_path = tmp_path / "manifest.yaml"

    matched = export_source_files(project, manifest_path, "core")

    assert matched == ["core"]
    files_root = tmp_path / "manifest.files"
    copied_java = (
        files_root
        / "core"
        / "src"
        / "main"
        / "java"
        / "com"
        / "example"
        / "core"
        / "Core.java"
    )
    assert copied_java.is_file()
    original_java = (
        project_root
        / "core"
        / "src"
        / "main"
        / "java"
        / "com"
        / "example"
        / "core"
        / "Core.java"
    )
    assert copied_java.read_text() == original_java.read_text()
    assert not (files_root / "api").exists()
    assert not (files_root / "multi-module-demo-bom").exists()


def test_export_source_files_supports_glob_pattern(project_root, tmp_path):
    project = MavenAdapter().infer_structure(project_root)
    manifest_path = tmp_path / "manifest.yaml"

    matched = export_source_files(project, manifest_path, "*-bom")

    assert matched == ["multi-module-demo-bom"]


def test_export_source_files_no_match_creates_nothing(project_root, tmp_path):
    project = MavenAdapter().infer_structure(project_root)
    manifest_path = tmp_path / "manifest.yaml"

    matched = export_source_files(project, manifest_path, "shared-*")

    assert matched == []
    assert not (tmp_path / "manifest.files").exists()
