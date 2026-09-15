import shutil
from pathlib import Path

import pytest

from manager.adapters.maven.adapter import MavenAdapter
from manager.models import ProjectMetadata

FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "maven-multi-module"


@pytest.fixture
def project_root(tmp_path) -> Path:
    dest = tmp_path / "project"
    shutil.copytree(FIXTURE_SOURCE, dest)
    return dest


def _metadata(artifact_id: str, **overrides) -> ProjectMetadata:
    return ProjectMetadata(artifact_id=artifact_id, **overrides)


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


def test_update_metadata_sets_name_and_description(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.update_metadata(
        project,
        "core",
        _metadata("core", name="Core Lib", description="Biblioteca core."),
    )
    core = _find(updated, "core")

    assert core.metadata.name == "Core Lib"
    assert core.metadata.description == "Biblioteca core."
    pom_text = (project_root / "core" / "pom.xml").read_text()
    assert "<description>Biblioteca core.</description>" in pom_text


def test_update_metadata_clears_optional_field(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    core = _find(project, "core")
    assert core.metadata.name == "Core"

    updated = adapter.update_metadata(project, "core", _metadata("core", name=None))
    core = _find(updated, "core")

    assert core.metadata.name is None
    pom_text = (project_root / "core" / "pom.xml").read_text()
    assert "<name>" not in pom_text


def test_update_metadata_inherits_group_id_and_version_when_equal_to_parent(
    project_root,
):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.update_metadata(
        project,
        "core",
        _metadata("core", group_id="com.example", version="1.0.0"),
    )
    core = _find(updated, "core")

    assert core.metadata.group_id == "com.example"
    assert core.metadata.version == "1.0.0"
    pom_text = (project_root / "core" / "pom.xml").read_text()
    segment = pom_text.split("</parent>")[1].split("<packaging>")[0]
    assert "<groupId>" not in segment
    assert "<version>" not in segment


def test_update_metadata_writes_explicit_group_id_when_it_differs_from_parent(
    project_root,
):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.update_metadata(
        project, "core", _metadata("core", group_id="com.other")
    )
    core = _find(updated, "core")

    assert core.metadata.group_id == "com.other"
    pom_text = (project_root / "core" / "pom.xml").read_text()
    assert "<groupId>com.other</groupId>" in pom_text


def test_update_metadata_updates_java_version_properties(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.update_metadata(
        project,
        "multi-module-demo",
        _metadata(
            "multi-module-demo",
            group_id="com.example",
            version="1.0.0",
            packaging="pom",
            properties={"maven.compiler.source": "21"},
        ),
    )
    root_module = updated.root_module

    assert root_module.metadata.properties["maven.compiler.source"] == "21"
    assert root_module.metadata.properties["maven.compiler.target"] == "21"


def test_update_metadata_creates_properties_section_when_missing(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.update_metadata(
        project, "core", _metadata("core", properties={"maven.compiler.source": "21"})
    )
    core = _find(updated, "core")

    assert core.metadata.properties["maven.compiler.source"] == "21"
    assert core.metadata.properties["maven.compiler.target"] == "21"


def test_update_metadata_clears_java_version_and_removes_empty_properties(
    project_root,
):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.update_metadata(
        project,
        "multi-module-demo",
        _metadata(
            "multi-module-demo",
            group_id="com.example",
            version="1.0.0",
            packaging="pom",
        ),
    )
    root_module = updated.root_module

    assert "maven.compiler.source" not in root_module.metadata.properties
    pom_text = (project_root / "pom.xml").read_text()
    assert "<properties>" not in pom_text


def test_update_metadata_rejects_artifact_id_rename(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="artifactId"):
        adapter.update_metadata(project, "core", _metadata("core-renamed"))


def test_update_metadata_rejects_packaging_change_on_bom_module(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="packaging"):
        adapter.update_metadata(
            project,
            "multi-module-demo-bom",
            _metadata("multi-module-demo-bom", packaging="jar"),
        )


def test_update_metadata_requires_group_id_and_version_on_root_module(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="raiz"):
        adapter.update_metadata(
            project,
            "multi-module-demo",
            _metadata(
                "multi-module-demo", group_id=None, version=None, packaging="pom"
            ),
        )


def test_update_metadata_result_matches_fresh_inference(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.update_metadata(
        project, "core", _metadata("core", description="Nova descricao")
    )
    reinferred = adapter.infer_structure(project_root)

    core_updated = _find(updated, "core")
    core_reinferred = _find(reinferred, "core")
    assert core_updated.metadata.description == core_reinferred.metadata.description
