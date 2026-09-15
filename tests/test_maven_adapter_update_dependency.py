import shutil
from pathlib import Path

import pytest

from manager.adapters.maven.adapter import MavenAdapter
from manager.models import Dependency

FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "maven-multi-module"


@pytest.fixture
def project_root(tmp_path) -> Path:
    dest = tmp_path / "project"
    shutil.copytree(FIXTURE_SOURCE, dest)
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


def test_update_dependency_adds_new_managed_entry(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    dependency = Dependency(
        group_id="org.springframework.boot",
        artifact_id="spring-boot-dependencies",
        version="3.3.4",
        type="pom",
        scope="import",
        managed=True,
    )
    updated = adapter.update_dependency(project, "multi-module-demo-bom", dependency)

    names = {dep.artifact_id for dep in updated.managed_dependencies}
    assert "spring-boot-dependencies" in names
    pom_text = (project_root / "bom" / "pom.xml").read_text()
    assert "<artifactId>spring-boot-dependencies</artifactId>" in pom_text
    assert "<type>pom</type>" in pom_text
    assert "<scope>import</scope>" in pom_text


def test_update_dependency_updates_existing_entry_instead_of_duplicating(
    project_root,
):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    dependency = Dependency(
        group_id="org.apache.commons",
        artifact_id="commons-lang3",
        version="3.15.0",
        managed=True,
    )
    updated = adapter.update_dependency(project, "multi-module-demo-bom", dependency)

    matches = [
        dep
        for dep in updated.managed_dependencies
        if dep.artifact_id == "commons-lang3"
    ]
    assert len(matches) == 1
    assert matches[0].version == "3.15.0"
    pom_text = (project_root / "bom" / "pom.xml").read_text()
    assert pom_text.count("<artifactId>commons-lang3</artifactId>") == 1


def test_update_dependency_creates_dependency_management_when_missing(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    root_module = project.root_module
    dependency = Dependency(
        group_id="com.example", artifact_id="core", version="1.0.0", managed=True
    )
    updated = adapter.update_dependency(project, root_module.name, dependency)

    names = {dep.artifact_id for dep in updated.managed_dependencies}
    assert "core" in names
    pom_text = (project_root / "pom.xml").read_text()
    assert "<dependencyManagement>" in pom_text


def test_update_dependency_adds_direct_dependency(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    dependency = Dependency(
        group_id="com.example", artifact_id="core", version="1.0.0", managed=False
    )
    updated = adapter.update_dependency(project, "api", dependency)
    api = _find(updated, "api")

    assert any(
        dep.artifact_id == "core" and not dep.managed for dep in api.dependencies
    )


def test_update_dependency_rejects_missing_version_for_managed(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    dependency = Dependency(
        group_id="org.apache.commons", artifact_id="commons-io", managed=True
    )
    with pytest.raises(ValueError, match="version"):
        adapter.update_dependency(project, "multi-module-demo-bom", dependency)


def test_update_dependency_rejects_managed_entry_on_non_pom_module(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    dependency = Dependency(
        group_id="org.apache.commons",
        artifact_id="commons-io",
        version="2.16.1",
        managed=True,
    )
    with pytest.raises(ValueError, match="packaging"):
        adapter.update_dependency(project, "core", dependency)


def test_update_dependency_rejects_unknown_module(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    dependency = Dependency(
        group_id="org.apache.commons",
        artifact_id="commons-io",
        version="2.16.1",
        managed=True,
    )
    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.update_dependency(project, "inexistente", dependency)


def test_update_dependency_result_matches_fresh_inference(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    dependency = Dependency(
        group_id="org.apache.commons",
        artifact_id="commons-io",
        version="2.16.1",
        managed=True,
    )
    updated = adapter.update_dependency(project, "multi-module-demo-bom", dependency)
    reinferred = adapter.infer_structure(project_root)

    updated_names = {dep.artifact_id for dep in updated.managed_dependencies}
    reinferred_names = {dep.artifact_id for dep in reinferred.managed_dependencies}
    assert updated_names == reinferred_names
