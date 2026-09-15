import shutil
from pathlib import Path

import pytest

from manager.adapters.maven.adapter import MavenAdapter

FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "maven-multi-module"


@pytest.fixture
def project_root(tmp_path) -> Path:
    dest = tmp_path / "project"
    shutil.copytree(FIXTURE_SOURCE, dest)
    return dest


def test_remove_dependency_removes_existing_managed_entry(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.remove_dependency(project, "org.apache.commons", "commons-lang3")

    names = {dep.artifact_id for dep in updated.managed_dependencies}
    assert "commons-lang3" not in names
    pom_text = (project_root / "bom" / "pom.xml").read_text()
    assert "commons-lang3" not in pom_text


def test_remove_dependency_result_matches_fresh_inference(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.remove_dependency(project, "org.apache.commons", "commons-lang3")
    reinferred = adapter.infer_structure(project_root)

    assert updated == reinferred


def test_remove_dependency_removing_last_entry_clears_dependency_management(
    project_root,
):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.remove_dependency(project, "org.apache.commons", "commons-lang3")
    updated = adapter.remove_dependency(updated, "com.example", "core")

    assert updated.managed_dependencies == []
    pom_text = (project_root / "bom" / "pom.xml").read_text()
    assert "<dependencyManagement>" not in pom_text


def test_remove_dependency_rejects_unknown_dependency(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao encontrada"):
        adapter.remove_dependency(project, "com.unknown", "does-not-exist")


def test_remove_dependency_does_not_touch_direct_dependency_with_same_coordinates(
    project_root,
):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    # "api" tem uma dependencia direta (managed=False) para com.example:core;
    # remover a entrada gerenciada de com.example:core no BOM nao deve mexer
    # na <dependencies> direta de "api".

    updated = adapter.remove_dependency(project, "com.example", "core")

    api = next(m for m in updated.root_module.submodules if m.name == "api")
    assert any(
        dep.artifact_id == "core" and not dep.managed for dep in api.dependencies
    )
    pom_text = (project_root / "api" / "pom.xml").read_text()
    assert "<artifactId>core</artifactId>" in pom_text


def test_remove_dependency_does_not_mutate_versioned_fixture(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    adapter.remove_dependency(project, "org.apache.commons", "commons-lang3")

    fixture_pom = (FIXTURE_SOURCE / "bom" / "pom.xml").read_text()
    assert "commons-lang3" in fixture_pom
