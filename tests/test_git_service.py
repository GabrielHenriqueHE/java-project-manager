import subprocess
from pathlib import Path

import pytest

from manager.services.git import GitCloneError, clone_repository


def _run_git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def source_repo(tmp_path) -> Path:
    repo = tmp_path / "source-repo"
    repo.mkdir()
    (repo / "pom.xml").write_text("<project/>")
    _run_git("init", cwd=repo)
    _run_git("config", "user.email", "test@example.com", cwd=repo)
    _run_git("config", "user.name", "Test", cwd=repo)
    _run_git("add", ".", cwd=repo)
    _run_git("commit", "-m", "initial", cwd=repo)
    return repo


def test_clone_repository_clones_local_path(tmp_path, source_repo):
    destination = tmp_path / "cloned"

    clone_repository(str(source_repo), destination)

    assert (destination / "pom.xml").is_file()
    assert (destination / ".git").is_dir()


def test_clone_repository_rejects_nonexistent_source(tmp_path):
    destination = tmp_path / "cloned"

    with pytest.raises(GitCloneError):
        clone_repository(str(tmp_path / "does-not-exist"), destination)

    assert not destination.exists()


def test_clone_repository_rejects_non_empty_destination(tmp_path, source_repo):
    destination = tmp_path / "cloned"
    destination.mkdir()
    (destination / "file.txt").write_text("ja tinha algo aqui")

    with pytest.raises(GitCloneError, match="ja existe"):
        clone_repository(str(source_repo), destination)

    assert (destination / "file.txt").read_text() == "ja tinha algo aqui"


def test_clone_repository_allows_existing_empty_destination(tmp_path, source_repo):
    destination = tmp_path / "cloned"
    destination.mkdir()

    clone_repository(str(source_repo), destination)

    assert (destination / "pom.xml").is_file()


def test_clone_repository_rejects_missing_git_binary(monkeypatch, tmp_path, source_repo):
    monkeypatch.setattr("manager.services.git.shutil.which", lambda _: None)

    with pytest.raises(GitCloneError, match="git nao encontrado"):
        clone_repository(str(source_repo), tmp_path / "cloned")
