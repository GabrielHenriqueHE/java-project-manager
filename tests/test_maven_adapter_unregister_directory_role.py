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


def test_unregister_directory_role_removes_single_execution(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)
    project = adapter.register_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )

    updated = adapter.unregister_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )

    pom_text = (project_root / "core" / "pom.xml").read_text()
    assert "build-helper-maven-plugin" not in pom_text
    assert "<build>" not in pom_text
    core = next(m for m in updated.root_module.submodules if m.name == "core")
    assert "src/main/proto" not in core.directory_structure.source_dirs


def test_unregister_directory_role_keeps_other_executions(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)
    (project_root / "core" / "src" / "test" / "proto").mkdir(parents=True)
    project = adapter.register_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )
    project = adapter.register_directory_role(
        project, "core", Path("src/test/proto"), "test-source"
    )

    adapter.unregister_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )

    pom_text = (project_root / "core" / "pom.xml").read_text()
    assert "build-helper-maven-plugin" in pom_text
    assert pom_text.count("<execution>") == 1
    assert "<source>src/test/proto</source>" in pom_text
    assert "<source>src/main/proto</source>" not in pom_text


def test_unregister_directory_role_directory_stays_on_disk(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    proto_dir = project_root / "core" / "src" / "main" / "proto"
    proto_dir.mkdir(parents=True)
    project = adapter.register_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )

    adapter.unregister_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )

    assert proto_dir.is_dir()


def test_unregister_directory_role_rejects_not_registered(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao esta registrado"):
        adapter.unregister_directory_role(
            project, "core", Path("src/main/proto"), "source"
        )


def test_unregister_directory_role_rejects_mismatched_role(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)
    project = adapter.register_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )

    with pytest.raises(ValueError, match="nao esta registrado"):
        adapter.unregister_directory_role(
            project, "core", Path("src/main/proto"), "resource"
        )


def test_unregister_directory_role_rejects_invalid_role(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="role invalido"):
        adapter.unregister_directory_role(
            project, "core", Path("src/main/proto"), "other"
        )


def test_unregister_directory_role_rejects_unknown_module(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.unregister_directory_role(
            project, "inexistente", Path("src/main/proto"), "source"
        )


def test_unregister_directory_role_does_not_mutate_versioned_fixture(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)
    project = adapter.register_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )

    adapter.unregister_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )

    fixture_pom = (FIXTURE_SOURCE / "core" / "pom.xml").read_text()
    assert "build-helper-maven-plugin" not in fixture_pom
