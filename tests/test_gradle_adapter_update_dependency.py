import shutil
from pathlib import Path

import pytest

from manager.adapters.gradle.adapter import GradleAdapter
from manager.models import Dependency

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


def _find(project, name):
    def walk(module):
        if module.name == name:
            return module
        for sub in module.submodules:
            found = walk(sub)
            if found is not None:
                return found
        return None

    return walk(project.root_module)


@pytest.mark.parametrize("root_fixture", ["groovy_root", "kotlin_root"])
def test_update_dependency_adds_new_managed_entry(root_fixture, request):
    project_root = request.getfixturevalue(root_fixture)
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)

    dependency = Dependency(
        group_id="org.springframework.boot",
        artifact_id="spring-boot-dependencies",
        version="3.3.4",
        managed=True,
    )
    updated = adapter.update_dependency(project, "bom", dependency)

    names = {dep.artifact_id for dep in updated.managed_dependencies}
    assert "spring-boot-dependencies" in names


def test_update_dependency_updates_existing_managed_entry_in_place(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    dependency = Dependency(
        group_id="org.apache.commons",
        artifact_id="commons-lang3",
        version="3.15.0",
        managed=True,
    )
    updated = adapter.update_dependency(project, "bom", dependency)

    matches = [
        dep
        for dep in updated.managed_dependencies
        if dep.artifact_id == "commons-lang3"
    ]
    assert len(matches) == 1
    assert matches[0].version == "3.15.0"
    build_text = (groovy_root / "bom" / "build.gradle").read_text()
    assert build_text.count("commons-lang3") == 1


def test_update_dependency_updates_existing_direct_entry_in_place(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    dependency = Dependency(
        group_id="org.junit.jupiter", artifact_id="junit-jupiter", version="5.11.0"
    )
    updated = adapter.update_dependency(project, "core", dependency)
    core = _find(updated, "core")

    matches = [dep for dep in core.dependencies if dep.artifact_id == "junit-jupiter"]
    assert len(matches) == 1
    assert matches[0].version == "5.11.0"
    build_text = (groovy_root / "core" / "build.gradle").read_text()
    assert build_text.count("junit-jupiter") == 1


def test_update_dependency_creates_dependencies_block_when_missing(tmp_path):
    (tmp_path / "settings.gradle").write_text(
        "rootProject.name = 'demo'\ninclude 'leaf'\n"
    )
    leaf_dir = tmp_path / "leaf"
    leaf_dir.mkdir()
    (leaf_dir / "build.gradle").write_text(
        "plugins {\n    id 'java-library'\n}\n\ngroup = 'com.example'\nversion = '1.0.0'\n"
    )

    adapter = GradleAdapter()
    project = adapter.infer_structure(tmp_path)

    dependency = Dependency(group_id="com.example", artifact_id="core", version="1.0.0")
    updated = adapter.update_dependency(project, "leaf", dependency)
    leaf = _find(updated, "leaf")

    assert any(dep.artifact_id == "core" for dep in leaf.dependencies)
    build_text = (leaf_dir / "build.gradle").read_text()
    assert "dependencies {" in build_text


def test_update_dependency_adds_direct_dependency(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    dependency = Dependency(
        group_id="com.google.guava", artifact_id="guava", version="33.0.0-jre"
    )
    updated = adapter.update_dependency(project, "api", dependency)
    api = _find(updated, "api")

    assert any(
        dep.artifact_id == "guava" and not dep.managed for dep in api.dependencies
    )


def test_update_dependency_adds_direct_dependency_with_scope_mapping(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    dependency = Dependency(
        group_id="org.projectlombok",
        artifact_id="lombok",
        version="1.18.32",
        scope="provided",
    )
    adapter.update_dependency(project, "api", dependency)

    build_text = (groovy_root / "api" / "build.gradle").read_text()
    assert "compileOnly 'org.projectlombok:lombok:1.18.32'" in build_text


def test_update_dependency_rejects_missing_version_for_managed(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    dependency = Dependency(
        group_id="org.apache.commons", artifact_id="commons-io", managed=True
    )
    with pytest.raises(ValueError, match="version"):
        adapter.update_dependency(project, "bom", dependency)


def test_update_dependency_rejects_managed_entry_on_non_pom_module(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    dependency = Dependency(
        group_id="org.apache.commons",
        artifact_id="commons-io",
        version="2.16.1",
        managed=True,
    )
    with pytest.raises(ValueError, match="packaging"):
        adapter.update_dependency(project, "core", dependency)


def test_update_dependency_rejects_missing_group_or_artifact(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="obrigatorios"):
        adapter.update_dependency(
            project, "core", Dependency(group_id="", artifact_id="x")
        )


def test_update_dependency_rejects_unknown_module(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    dependency = Dependency(
        group_id="org.apache.commons",
        artifact_id="commons-io",
        version="2.16.1",
        managed=True,
    )
    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.update_dependency(project, "inexistente", dependency)


def test_update_dependency_rejects_module_without_build_file(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    dependency = Dependency(group_id="com.example", artifact_id="core", version="1.0.0")
    with pytest.raises(ValueError, match="build.gradle"):
        adapter.update_dependency(project, "multi-module-demo", dependency)


def test_update_dependency_result_matches_fresh_inference(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    dependency = Dependency(
        group_id="org.apache.commons",
        artifact_id="commons-io",
        version="2.16.1",
        managed=True,
    )
    updated = adapter.update_dependency(project, "bom", dependency)
    reinferred = adapter.infer_structure(groovy_root)

    updated_names = {dep.artifact_id for dep in updated.managed_dependencies}
    reinferred_names = {dep.artifact_id for dep in reinferred.managed_dependencies}
    assert updated_names == reinferred_names
