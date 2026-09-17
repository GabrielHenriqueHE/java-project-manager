import shutil
from pathlib import Path

import pytest

from manager.adapters.base import DependentModuleConflict
from manager.adapters.gradle.adapter import GradleAdapter
from manager.models import Module

FIXTURES = Path(__file__).parent / "fixtures"
GROOVY_SOURCE = FIXTURES / "gradle-multi-module-groovy"
KOTLIN_SOURCE = FIXTURES / "gradle-multi-module-kotlin"


@pytest.fixture
def groovy_root(tmp_path) -> Path:
    dest = tmp_path / "project"
    shutil.copytree(GROOVY_SOURCE, dest)
    return dest


@pytest.fixture
def kotlin_root(tmp_path) -> Path:
    dest = tmp_path / "project"
    shutil.copytree(KOTLIN_SOURCE, dest)
    return dest


def _flatten_names(module: Module) -> set[str]:
    names = {module.name}
    for sub in module.submodules:
        names |= _flatten_names(sub)
    return names


@pytest.mark.parametrize("root_fixture", ["groovy_root", "kotlin_root"])
def test_remove_module_without_dependents_succeeds(root_fixture, request):
    project_root = request.getfixturevalue(root_fixture)
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.remove_module(project, "api")

    assert "api" not in _flatten_names(updated.root_module)


def test_remove_module_does_not_delete_module_directory(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    adapter.remove_module(project, "api")

    assert (groovy_root / "api").is_dir()


def test_remove_module_with_dependents_raises_without_force(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(DependentModuleConflict) as exc_info:
        adapter.remove_module(project, "core")

    assert exc_info.value.module_name == "core"
    assert exc_info.value.dependents == ["api"]


def test_remove_module_with_force_removes_dependent_dependency(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.remove_module(project, "core", force=True)

    names = _flatten_names(updated.root_module)
    assert "core" not in names

    api = next(
        m
        for m in [updated.root_module, *updated.root_module.submodules]
        if m.name == "api"
    )
    assert all(dep.artifact_id != "core" for dep in api.dependencies)


def test_remove_module_removes_managed_dependency_from_bom(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.remove_module(project, "core", force=True)

    assert all(dep.artifact_id != "core" for dep in updated.managed_dependencies)
    assert any(
        dep.artifact_id == "commons-lang3" for dep in updated.managed_dependencies
    )


def test_remove_module_updates_settings_file_on_disk(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    adapter.remove_module(project, "core", force=True)

    settings_text = (groovy_root / "settings.gradle").read_text()
    assert "'core'" not in settings_text
    assert "'bom'" in settings_text
    assert "'api'" in settings_text


def test_remove_nonexistent_module_raises_value_error(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.remove_module(project, "nao-existe")


def test_remove_root_module_raises_value_error(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="raiz"):
        adapter.remove_module(project, project.root_module.name)


def test_remove_module_result_matches_fresh_inference(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.remove_module(project, "api")
    reinferred = adapter.infer_structure(groovy_root)

    assert _flatten_names(reinferred.root_module) == _flatten_names(updated.root_module)
