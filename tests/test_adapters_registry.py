import shutil
from pathlib import Path

from manager.adapters.gradle.adapter import GradleAdapter
from manager.adapters.maven.adapter import MavenAdapter
from manager.services.adapters_registry import detect_adapter

FIXTURES = Path(__file__).parent / "fixtures"


def test_detect_adapter_routes_maven_project(tmp_path):
    dest = tmp_path / "project"
    shutil.copytree(FIXTURES / "maven-multi-module", dest)

    assert isinstance(detect_adapter(dest), MavenAdapter)


def test_detect_adapter_routes_gradle_groovy_project(tmp_path):
    dest = tmp_path / "project"
    shutil.copytree(FIXTURES / "gradle-multi-module-groovy", dest)

    assert isinstance(detect_adapter(dest), GradleAdapter)


def test_detect_adapter_routes_gradle_kotlin_project(tmp_path):
    dest = tmp_path / "project"
    shutil.copytree(FIXTURES / "gradle-multi-module-kotlin", dest)

    assert isinstance(detect_adapter(dest), GradleAdapter)


def test_detect_adapter_returns_none_for_unknown_dir(tmp_path):
    assert detect_adapter(tmp_path) is None
