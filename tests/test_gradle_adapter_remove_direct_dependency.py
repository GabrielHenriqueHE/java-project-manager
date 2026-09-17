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
def test_remove_direct_dependency_removes_existing_entry(root_fixture, request):
    project_root = request.getfixturevalue(root_fixture)
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)
    # "api" tem uma dependencia direta (managed=False) para com.example:core.

    updated = adapter.remove_direct_dependency(project, "api", "com.example", "core")

    api = next(m for m in updated.root_module.submodules if m.name == "api")
    assert not any(
        dep.artifact_id == "core" and not dep.managed for dep in api.dependencies
    )


def test_remove_direct_dependency_collapses_empty_dependencies_block(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    adapter.remove_direct_dependency(project, "api", "com.example", "core")

    build_text = (groovy_root / "api" / "build.gradle").read_text()
    assert "dependencies" not in build_text


def test_remove_direct_dependency_result_matches_fresh_inference(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.remove_direct_dependency(project, "api", "com.example", "core")
    reinferred = adapter.infer_structure(groovy_root)

    assert updated == reinferred


def test_remove_direct_dependency_does_not_touch_managed_entry_with_same_coordinates(
    groovy_root,
):
    # com.example:core tambem existe como dependencia GERENCIADA no "bom";
    # remover a direta de "api" nao deve mexer no bom.
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.remove_direct_dependency(project, "api", "com.example", "core")

    names = {dep.artifact_id for dep in updated.managed_dependencies}
    assert "core" in names


def test_remove_direct_dependency_rejects_unknown_dependency(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="nao encontrada"):
        adapter.remove_direct_dependency(
            project, "api", "com.unknown", "does-not-exist"
        )


def test_remove_direct_dependency_rejects_managed_only_coordinates_as_direct(
    groovy_root,
):
    # org.apache.commons:commons-lang3 so existe como gerenciada (constraints
    # do "bom"), nunca como direta em nenhum modulo -- nao deve ser removivel
    # por essa via.
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="nao encontrada"):
        adapter.remove_direct_dependency(
            project, "bom", "org.apache.commons", "commons-lang3"
        )


def test_remove_direct_dependency_rejects_unknown_module(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.remove_direct_dependency(project, "inexistente", "com.example", "core")


def test_remove_direct_dependency_does_not_mutate_versioned_fixture(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    adapter.remove_direct_dependency(project, "api", "com.example", "core")

    fixture_build = (GROOVY_SOURCE / "api" / "build.gradle").read_text()
    assert "com.example:core" in fixture_build
