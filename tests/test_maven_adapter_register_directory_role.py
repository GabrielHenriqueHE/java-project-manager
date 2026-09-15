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


def test_register_directory_role_creates_build_from_scratch(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)

    adapter.register_directory_role(project, "core", Path("src/main/proto"), "source")

    pom_text = (project_root / "core" / "pom.xml").read_text()
    assert "<build>" in pom_text
    assert "<artifactId>build-helper-maven-plugin</artifactId>" in pom_text
    assert "<groupId>org.codehaus.mojo</groupId>" in pom_text
    assert "<goal>add-source</goal>" in pom_text
    assert "<phase>generate-sources</phase>" in pom_text
    assert "<source>src/main/proto</source>" in pom_text
    # cada tag aninhada nova fica na sua propria linha, indentada (nao colada
    # na tag de abertura do pai) - ver bug corrigido em xml_utils.
    assert "<build>\n    <plugins>\n      <plugin>\n" in pom_text
    assert "<executions>\n          <execution>\n" in pom_text


def test_register_directory_role_resource_uses_resources_element(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "extra-resources").mkdir(parents=True)

    adapter.register_directory_role(
        project, "core", Path("src/main/extra-resources"), "resource"
    )

    pom_text = (project_root / "core" / "pom.xml").read_text()
    assert "<goal>add-resource</goal>" in pom_text
    assert "<phase>generate-resources</phase>" in pom_text
    assert "<directory>src/main/extra-resources</directory>" in pom_text


def test_register_directory_role_reuses_existing_plugin_for_second_entry(
    project_root,
):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)
    (project_root / "core" / "src" / "test" / "proto").mkdir(parents=True)

    project = adapter.register_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )
    adapter.register_directory_role(
        project, "core", Path("src/test/proto"), "test-source"
    )

    pom_text = (project_root / "core" / "pom.xml").read_text()
    assert pom_text.count("<artifactId>build-helper-maven-plugin</artifactId>") == 1
    assert pom_text.count("<execution>") == 2


def test_register_directory_role_is_idempotent(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)

    project = adapter.register_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )
    pom_text_after_first = (project_root / "core" / "pom.xml").read_text()

    adapter.register_directory_role(project, "core", Path("src/main/proto"), "source")
    pom_text_after_second = (project_root / "core" / "pom.xml").read_text()

    assert pom_text_after_first == pom_text_after_second
    assert pom_text_after_second.count("<execution>") == 1


def test_register_directory_role_rejects_missing_directory(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao existe"):
        adapter.register_directory_role(
            project, "core", Path("src/main/proto"), "source"
        )


def test_register_directory_role_rejects_invalid_role(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)

    with pytest.raises(ValueError, match="role invalido"):
        adapter.register_directory_role(
            project, "core", Path("src/main/proto"), "other"
        )


def test_register_directory_role_rejects_unknown_module(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.register_directory_role(
            project, "inexistente", Path("src/main/proto"), "source"
        )


def test_register_directory_role_does_not_mutate_versioned_fixture(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)

    adapter.register_directory_role(project, "core", Path("src/main/proto"), "source")

    fixture_pom = (FIXTURE_SOURCE / "core" / "pom.xml").read_text()
    assert "build-helper-maven-plugin" not in fixture_pom
