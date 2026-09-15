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


def test_add_directory_creates_missing_directory(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    adapter.add_directory(project, "core", Path("src/main/resources"))

    assert (project_root / "core" / "src" / "main" / "resources").is_dir()


def test_add_directory_creates_intermediate_parents(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    adapter.add_directory(project, "core", Path("src/main/webapp"))

    assert (project_root / "core" / "src" / "main" / "webapp").is_dir()


def test_add_directory_returns_reinferred_project(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.add_directory(project, "core", Path("src/main/resources"))

    assert updated == adapter.infer_structure(project_root)


def test_add_directory_rejects_existing_directory(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="ja existe"):
        adapter.add_directory(project, "core", Path("src/main/java"))


def test_add_directory_rejects_unknown_module(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.add_directory(project, "inexistente", Path("src/main/resources"))


def test_add_directory_rejects_path_traversal(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="escapa"):
        adapter.add_directory(project, "core", Path("../../etc"))

    assert not (project_root.parent.parent / "etc").exists()


def test_add_directory_does_not_mutate_versioned_fixture(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    adapter.add_directory(project, "core", Path("docs"))

    assert not (FIXTURE_SOURCE / "core" / "docs").exists()
