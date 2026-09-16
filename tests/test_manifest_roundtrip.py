import shutil
from pathlib import Path

from manager.adapters.maven.adapter import MavenAdapter
from manager.manifest import dump_manifest, load_manifest, to_manifest
from manager.models import Module

FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "maven-multi-module"


def _flatten(module: Module) -> list[Module]:
    result = [module]
    for sub in module.submodules:
        result.extend(_flatten(sub))
    return result


def _module_shape(module: Module) -> dict:
    return {
        "packaging": module.metadata.packaging,
        "is_bom": module.is_bom,
        "dependencies": sorted(
            (dep.group_id, dep.artifact_id, dep.version, dep.managed)
            for dep in module.dependencies
        ),
        "source_dirs": sorted(module.directory_structure.source_dirs),
        "test_dirs": sorted(module.directory_structure.test_dirs),
        "resource_dirs": sorted(module.directory_structure.resource_dirs),
        "test_resource_dirs": sorted(module.directory_structure.test_resource_dirs),
        "submodule_ids": sorted(sub.metadata.artifact_id for sub in module.submodules),
    }


def test_export_then_create_project_reproduces_equivalent_structure(tmp_path):
    original_root = tmp_path / "original"
    shutil.copytree(FIXTURE_SOURCE, original_root)
    adapter = MavenAdapter()

    original_project = adapter.infer_structure(original_root)

    manifest = to_manifest(original_project.root_module)
    manifest_path = tmp_path / "manifest.yaml"
    dump_manifest(manifest, manifest_path)

    loaded_manifest = load_manifest(manifest_path)
    recreated_project = adapter.create_project(loaded_manifest, tmp_path / "recreated")

    original_shapes = {
        module.metadata.artifact_id: _module_shape(module)
        for module in _flatten(original_project.root_module)
    }
    recreated_shapes = {
        module.metadata.artifact_id: _module_shape(module)
        for module in _flatten(recreated_project.root_module)
    }

    assert set(original_shapes) == set(recreated_shapes)
    for artifact_id, shape in original_shapes.items():
        assert recreated_shapes[artifact_id] == shape, artifact_id

    original_managed = sorted(
        (dep.group_id, dep.artifact_id, dep.version)
        for dep in original_project.managed_dependencies
    )
    recreated_managed = sorted(
        (dep.group_id, dep.artifact_id, dep.version)
        for dep in recreated_project.managed_dependencies
    )
    assert original_managed == recreated_managed
