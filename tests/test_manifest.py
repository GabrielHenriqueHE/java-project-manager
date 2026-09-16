import pytest

from manager.manifest import (
    ModuleManifest,
    is_bom_manifest,
    load_manifest,
    validate_manifest_tree,
)
from manager.models import Dependency, ProjectMetadata


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
