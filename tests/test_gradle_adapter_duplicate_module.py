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


def _module_names(project) -> set[str]:
    return {m.name for m in [project.root_module, *project.root_module.submodules]}


@pytest.mark.parametrize("root_fixture", ["groovy_root", "kotlin_root"])
def test_duplicate_module_copies_build_file_and_registers_include(
    root_fixture, request
):
    project_root = request.getfixturevalue(root_fixture)
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.duplicate_module(project, "core", "core-copy")

    assert "core-copy" in _module_names(updated)
    copy = next(m for m in updated.root_module.submodules if m.name == "core-copy")
    assert copy.metadata.group_id == "com.example"
    assert copy.metadata.version == "1.0.0"
    assert copy.metadata.packaging == "jar"


def test_duplicate_module_preserves_dialect_and_content_groovy(groovy_root):
    (groovy_root / "core" / "src" / "main" / "java" / "com" / "example").mkdir(
        parents=True, exist_ok=True
    )
    marker = (
        groovy_root
        / "core"
        / "src"
        / "main"
        / "java"
        / "com"
        / "example"
        / "Marker.java"
    )
    marker.write_text("package com.example; class Marker {}")

    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    adapter.duplicate_module(project, "core", "core-copy")

    assert (groovy_root / "core-copy" / "build.gradle").is_file()
    assert not (groovy_root / "core-copy" / "build.gradle.kts").exists()
    settings_text = (groovy_root / "settings.gradle").read_text()
    assert "'core-copy'" in settings_text
    copied_marker = (
        groovy_root
        / "core-copy"
        / "src"
        / "main"
        / "java"
        / "com"
        / "example"
        / "Marker.java"
    )
    assert copied_marker.read_text() == "package com.example; class Marker {}"
    # 'java-library' e demais plugins customizados do build.gradle fonte
    # sao preservados por ser copia literal (diferente de add_module, que
    # regenera o arquivo do zero a partir de metadados).
    build_text = (groovy_root / "core-copy" / "build.gradle").read_text()
    assert "java-library" in build_text


def test_duplicate_module_preserves_dialect_kotlin(kotlin_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(kotlin_root)

    adapter.duplicate_module(project, "core", "core-copy")

    assert (kotlin_root / "core-copy" / "build.gradle.kts").is_file()
    settings_text = (kotlin_root / "settings.gradle.kts").read_text()
    assert '"core-copy"' in settings_text


def test_duplicate_module_overrides_group_and_version(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.duplicate_module(
        project, "core", "core-copy", group_id="com.other", version="9.9.9"
    )
    copy = next(m for m in updated.root_module.submodules if m.name == "core-copy")

    assert copy.metadata.group_id == "com.other"
    assert copy.metadata.version == "9.9.9"


def test_duplicate_module_without_overrides_inherits_from_source(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.duplicate_module(project, "core", "core-copy")
    copy = next(m for m in updated.root_module.submodules if m.name == "core-copy")

    assert copy.metadata.group_id == "com.example"
    assert copy.metadata.version == "1.0.0"


def test_duplicate_module_accepts_explicit_root_as_parent(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.duplicate_module(
        project, "core", "core-copy", parent_name=project.root_module.name
    )

    assert "core-copy" in _module_names(updated)


def test_duplicate_module_rejects_non_root_parent(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="raiz"):
        adapter.duplicate_module(project, "core", "core-copy", parent_name="api")


def test_duplicate_module_rejects_duplicate_name(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="Ja existe"):
        adapter.duplicate_module(project, "core", "api")


def test_duplicate_module_rejects_existing_directory(groovy_root):
    (groovy_root / "assets").mkdir()

    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="ja existe"):
        adapter.duplicate_module(project, "core", "assets")


def test_duplicate_module_rejects_unknown_source(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.duplicate_module(project, "inexistente", "core-copy")


def test_duplicate_module_rejects_source_with_submodules(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="submodulos"):
        adapter.duplicate_module(
            project, project.root_module.name, "root-copy"
        )


def test_duplicate_module_rejects_unknown_parent(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.duplicate_module(
            project, "core", "core-copy", parent_name="inexistente"
        )


def test_duplicate_module_result_matches_fresh_inference(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.duplicate_module(project, "core", "core-copy")
    reinferred = adapter.infer_structure(groovy_root)

    assert _module_names(reinferred) == _module_names(updated)
