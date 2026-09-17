import shutil
from pathlib import Path

import pytest

from manager.adapters.base import DirectoryNotEmptyConflict
from manager.adapters.gradle.adapter import GradleAdapter

FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "gradle-multi-module-groovy"


@pytest.fixture
def project_root(tmp_path) -> Path:
    dest = tmp_path / "project"
    shutil.copytree(FIXTURE_SOURCE, dest)
    return dest


def test_remove_directory_removes_empty_directory(project_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)
    empty_dir = project_root / "core" / "src" / "main" / "resources"
    empty_dir.mkdir(parents=True)

    adapter.remove_directory(project, "core", Path("src/main/resources"))

    assert not empty_dir.exists()


def test_remove_directory_returns_reinferred_project(project_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "resources").mkdir(parents=True)

    updated = adapter.remove_directory(project, "core", Path("src/main/resources"))

    assert updated == adapter.infer_structure(project_root)


def test_remove_directory_rejects_non_empty_directory(project_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)
    # src/main/java do "core" ja tem Core.java (nao esta vazio).

    with pytest.raises(DirectoryNotEmptyConflict, match="nao esta vazio"):
        adapter.remove_directory(project, "core", Path("src/main/java"))

    assert (project_root / "core" / "src" / "main" / "java").exists()


def test_remove_directory_force_removes_non_empty_directory_recursively(project_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)
    target = project_root / "core" / "src" / "main" / "java"
    assert any(target.rglob("*"))

    adapter.remove_directory(project, "core", Path("src/main/java"), force=True)

    assert not target.exists()


def test_remove_directory_force_still_removes_empty_directory(project_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)
    empty_dir = project_root / "core" / "src" / "main" / "resources"
    empty_dir.mkdir(parents=True)

    adapter.remove_directory(project, "core", Path("src/main/resources"), force=True)

    assert not empty_dir.exists()


def test_remove_directory_force_does_not_bypass_module_root_guard(project_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="raiz do modulo"):
        adapter.remove_directory(project, "core", Path("."), force=True)


def test_remove_directory_rejects_missing_directory(project_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao existe"):
        adapter.remove_directory(project, "core", Path("src/main/resources"))


def test_remove_directory_rejects_unknown_module(project_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.remove_directory(project, "inexistente", Path("src/main/resources"))


def test_remove_directory_rejects_path_traversal(project_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="escapa"):
        adapter.remove_directory(project, "core", Path("../../etc"))


def test_remove_directory_rejects_module_root(project_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="raiz do modulo"):
        adapter.remove_directory(project, "core", Path("."))


def test_remove_directory_does_not_mutate_versioned_fixture(project_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "docs").mkdir()

    adapter.remove_directory(project, "core", Path("docs"))

    assert not (FIXTURE_SOURCE / "core" / "docs").exists()
