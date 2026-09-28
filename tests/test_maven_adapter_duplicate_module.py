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


def _module_names(project) -> set[str]:
    return {m.name for m in [project.root_module, *project.root_module.submodules]}


def _add_aggregator_with_existing_modules_section(project_root: Path) -> None:
    """Cria um segundo agregador ('agg', com um submodulo 'placeholder' e
    <modules> ja existente) para testar reparenting - nenhum modulo do
    fixture padrao serve (so a raiz tem <modules>; 'bom' e packaging=pom
    mas sem <modules> previo, como o proprio teste de add_module ja
    documenta)."""
    agg_dir = project_root / "agg"
    agg_dir.mkdir()
    (agg_dir / "pom.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>com.example</groupId>
    <artifactId>multi-module-demo</artifactId>
    <version>1.0.0</version>
  </parent>
  <artifactId>agg</artifactId>
  <packaging>pom</packaging>
  <modules>
    <module>placeholder</module>
  </modules>
</project>
"""
    )
    placeholder_dir = agg_dir / "placeholder"
    placeholder_dir.mkdir()
    (placeholder_dir / "pom.xml").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>com.example</groupId>
    <artifactId>agg</artifactId>
    <version>1.0.0</version>
  </parent>
  <artifactId>placeholder</artifactId>
  <packaging>jar</packaging>
</project>
"""
    )
    root_pom = project_root / "pom.xml"
    root_pom.write_text(
        root_pom.read_text().replace(
            "<module>bom</module>", "<module>bom</module>\n    <module>agg</module>"
        )
    )


def test_duplicate_module_copies_tree_and_registers_sibling(project_root):
    (project_root / "core" / "src" / "main" / "java" / "com" / "example").mkdir(
        parents=True, exist_ok=True
    )
    marker = (
        project_root
        / "core"
        / "src"
        / "main"
        / "java"
        / "com"
        / "example"
        / "Marker.java"
    )
    marker.write_text("package com.example; class Marker {}")

    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.duplicate_module(project, "core", "core-copy")

    assert "core-copy" in _module_names(updated)
    assert (
        project_root / "pom.xml"
    ).read_text().count("<module>core-copy</module>") == 1
    copied_marker = (
        project_root
        / "core-copy"
        / "src"
        / "main"
        / "java"
        / "com"
        / "example"
        / "Marker.java"
    )
    assert copied_marker.read_text() == "package com.example; class Marker {}"

    copy = next(m for m in updated.root_module.submodules if m.name == "core-copy")
    assert copy.metadata.group_id == "com.example"
    assert copy.metadata.version == "1.0.0"
    assert any(dep.artifact_id == "commons-lang3" for dep in copy.dependencies)


def test_duplicate_module_artifact_id_matches_new_name(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    adapter.duplicate_module(project, "core", "core-copy")

    pom_text = (project_root / "core-copy" / "pom.xml").read_text()
    assert "<artifactId>core-copy</artifactId>" in pom_text
    assert "<artifactId>core</artifactId>" not in pom_text


def test_duplicate_module_default_parent_keeps_original_parent_block(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    adapter.duplicate_module(project, "core", "core-copy")

    pom_text = (project_root / "core-copy" / "pom.xml").read_text()
    parent_block = pom_text.split("<parent>")[1].split("</parent>")[0]
    assert "<artifactId>multi-module-demo</artifactId>" in parent_block
    assert "<version>1.0.0</version>" in parent_block


def test_duplicate_module_explicit_parent_same_as_original_keeps_parent_block(
    project_root,
):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    adapter.duplicate_module(
        project, "core", "core-copy", parent_name="multi-module-demo"
    )

    pom_text = (project_root / "core-copy" / "pom.xml").read_text()
    parent_block = pom_text.split("<parent>")[1].split("</parent>")[0]
    assert "<artifactId>multi-module-demo</artifactId>" in parent_block


def test_duplicate_module_reparenting_rewrites_parent_block(project_root):
    _add_aggregator_with_existing_modules_section(project_root)

    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    adapter.duplicate_module(project, "core", "core-copy", parent_name="agg")

    pom_text = (project_root / "agg" / "core-copy" / "pom.xml").read_text()
    parent_block = pom_text.split("<parent>")[1].split("</parent>")[0]
    assert "<artifactId>agg</artifactId>" in parent_block
    assert (
        project_root / "agg" / "pom.xml"
    ).read_text().count("<module>core-copy</module>") == 1


def test_duplicate_module_overrides_group_and_version(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.duplicate_module(
        project, "core", "core-copy", group_id="com.other", version="9.9.9"
    )
    copy = next(m for m in updated.root_module.submodules if m.name == "core-copy")

    assert copy.metadata.group_id == "com.other"
    assert copy.metadata.version == "9.9.9"


def test_duplicate_module_without_overrides_inherits_from_source(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.duplicate_module(project, "core", "core-copy")
    copy = next(m for m in updated.root_module.submodules if m.name == "core-copy")

    assert copy.metadata.group_id == "com.example"
    assert copy.metadata.version == "1.0.0"


def test_duplicate_module_rejects_duplicate_name(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="Ja existe"):
        adapter.duplicate_module(project, "core", "api")


def test_duplicate_module_rejects_existing_directory(project_root):
    (project_root / "assets").mkdir()

    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="ja existe"):
        adapter.duplicate_module(project, "core", "assets")


def test_duplicate_module_rejects_unknown_source(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.duplicate_module(project, "inexistente", "core-copy")


def test_duplicate_module_rejects_source_with_submodules(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="submodulos"):
        adapter.duplicate_module(project, "multi-module-demo", "root-copy")


def test_duplicate_module_rejects_non_pom_explicit_parent(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="packaging"):
        adapter.duplicate_module(project, "api", "api-copy", parent_name="core")


def test_duplicate_module_rejects_unknown_parent(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.duplicate_module(
            project, "core", "core-copy", parent_name="inexistente"
        )


def test_duplicate_module_result_matches_fresh_inference(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.duplicate_module(project, "core", "core-copy")
    reinferred = adapter.infer_structure(project_root)

    assert _module_names(reinferred) == _module_names(updated)
