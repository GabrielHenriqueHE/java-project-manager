import shutil
from pathlib import Path

import pytest

from manager.adapters.base import DependentModuleConflict
from manager.adapters.maven.adapter import MavenAdapter
from manager.models import Module

FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "maven-multi-module"


@pytest.fixture
def project_root(tmp_path) -> Path:
    """Copia a fixture para um diretorio temporario, ja que remove_module
    escreve em disco e nao devemos mutar a fixture versionada no repo."""
    dest = tmp_path / "project"
    shutil.copytree(FIXTURE_SOURCE, dest)
    return dest


def _flatten_names(module: Module) -> set[str]:
    names = {module.name}
    for sub in module.submodules:
        names |= _flatten_names(sub)
    return names


def test_remove_module_without_dependents_succeeds(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.remove_module(project, "api")

    assert "api" not in _flatten_names(updated.root_module)


def test_remove_module_does_not_delete_module_directory(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    adapter.remove_module(project, "api")

    assert (project_root / "api").is_dir()


def test_remove_module_with_dependents_raises_without_force(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(DependentModuleConflict) as exc_info:
        adapter.remove_module(project, "core")

    assert exc_info.value.module_name == "core"
    assert exc_info.value.dependents == ["api"]


def test_remove_module_with_force_removes_dependent_dependency(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.remove_module(project, "core", force=True)

    names = _flatten_names(updated.root_module)
    assert "core" not in names

    api = next(
        m
        for m in [updated.root_module, *updated.root_module.submodules]
        if m.name == "api"
    )
    assert all(dep.artifact_id != "core" for dep in api.dependencies)


def test_remove_module_removes_managed_dependency_from_bom(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.remove_module(project, "core", force=True)

    assert all(dep.artifact_id != "core" for dep in updated.managed_dependencies)
    assert any(
        dep.artifact_id == "commons-lang3" for dep in updated.managed_dependencies
    )


def test_remove_module_updates_parent_pom_on_disk(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    adapter.remove_module(project, "core", force=True)

    parent_pom_text = (project_root / "pom.xml").read_text()
    assert "<module>core</module>" not in parent_pom_text
    assert "<module>bom</module>" in parent_pom_text
    assert "<module>api</module>" in parent_pom_text


def test_remove_nonexistent_module_raises_value_error(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.remove_module(project, "nao-existe")


def test_remove_root_module_raises_value_error(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="raiz"):
        adapter.remove_module(project, project.root_module.name)


def test_remove_module_result_matches_fresh_inference(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.remove_module(project, "api")
    reinferred = adapter.infer_structure(project_root)

    assert _flatten_names(reinferred.root_module) == _flatten_names(updated.root_module)
