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


def test_remove_direct_dependency_removes_existing_entry(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    # "api" tem uma dependencia direta (managed=False) para com.example:core.

    updated = adapter.remove_direct_dependency(project, "api", "com.example", "core")

    api = next(m for m in updated.root_module.submodules if m.name == "api")
    assert not any(
        dep.artifact_id == "core" and not dep.managed for dep in api.dependencies
    )
    pom_text = (project_root / "api" / "pom.xml").read_text()
    assert "<dependencies>" not in pom_text or "<artifactId>core</artifactId>" not in pom_text


def test_remove_direct_dependency_result_matches_fresh_inference(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.remove_direct_dependency(project, "api", "com.example", "core")
    reinferred = adapter.infer_structure(project_root)

    assert updated == reinferred


def test_remove_direct_dependency_does_not_touch_managed_entry_with_same_coordinates(
    project_root,
):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    # com.example:core tambem existe como dependencia GERENCIADA no BOM;
    # remover a direta de "api" nao deve mexer no BOM.

    updated = adapter.remove_direct_dependency(project, "api", "com.example", "core")

    names = {dep.artifact_id for dep in updated.managed_dependencies}
    assert "core" in names


def test_remove_direct_dependency_rejects_unknown_dependency(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao encontrada"):
        adapter.remove_direct_dependency(project, "api", "com.unknown", "does-not-exist")


def test_remove_direct_dependency_rejects_managed_only_coordinates_as_direct(
    project_root,
):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    # org.apache.commons:commons-lang3 so existe como gerenciada (BOM), nunca
    # como direta em nenhum modulo -- nao deve ser removivel por essa via.

    with pytest.raises(ValueError, match="nao encontrada"):
        adapter.remove_direct_dependency(
            project, "multi-module-demo-bom", "org.apache.commons", "commons-lang3"
        )


def test_remove_direct_dependency_rejects_unknown_module(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.remove_direct_dependency(
            project, "inexistente", "com.example", "core"
        )


def test_remove_direct_dependency_does_not_mutate_versioned_fixture(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    adapter.remove_direct_dependency(project, "api", "com.example", "core")

    fixture_pom = (FIXTURE_SOURCE / "api" / "pom.xml").read_text()
    assert "<artifactId>core</artifactId>" in fixture_pom
