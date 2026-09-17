import shutil
from pathlib import Path

import pytest

from manager.adapters.gradle.adapter import GradleAdapter

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


@pytest.mark.parametrize("root_fixture", ["groovy_root", "kotlin_root"])
def test_remove_dependency_removes_existing_managed_entry(root_fixture, request):
    project_root = request.getfixturevalue(root_fixture)
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.remove_dependency(project, "org.apache.commons", "commons-lang3")

    names = {dep.artifact_id for dep in updated.managed_dependencies}
    assert "commons-lang3" not in names


def test_remove_dependency_result_matches_fresh_inference(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.remove_dependency(project, "org.apache.commons", "commons-lang3")
    reinferred = adapter.infer_structure(groovy_root)

    assert updated == reinferred


def test_remove_dependency_removing_last_entry_collapses_constraints_and_dependencies(
    groovy_root,
):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.remove_dependency(project, "org.apache.commons", "commons-lang3")
    updated = adapter.remove_dependency(updated, "com.example", "core")

    assert updated.managed_dependencies == []
    build_text = (groovy_root / "bom" / "build.gradle").read_text()
    assert "constraints" not in build_text
    assert "dependencies" not in build_text


def test_remove_dependency_rejects_unknown_dependency(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="nao encontrada"):
        adapter.remove_dependency(project, "com.unknown", "does-not-exist")


def test_remove_dependency_does_not_touch_direct_dependency_with_same_coordinates(
    groovy_root,
):
    # "api" tem uma dependencia direta (managed=False) para com.example:core;
    # remover a entrada gerenciada de com.example:core no BOM nao deve mexer
    # na dependencia direta de "api".
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.remove_dependency(project, "com.example", "core")

    api = next(m for m in updated.root_module.submodules if m.name == "api")
    assert any(
        dep.artifact_id == "core" and not dep.managed for dep in api.dependencies
    )
    build_text = (groovy_root / "api" / "build.gradle").read_text()
    assert "com.example:core" in build_text


def test_remove_dependency_does_not_mutate_versioned_fixture(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    adapter.remove_dependency(project, "org.apache.commons", "commons-lang3")

    fixture_build = (GROOVY_SOURCE / "bom" / "build.gradle").read_text()
    assert "commons-lang3" in fixture_build
