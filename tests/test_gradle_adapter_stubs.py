from pathlib import Path

import pytest

from manager.adapters.gradle.adapter import GradleAdapter

FIXTURES = Path(__file__).parent / "fixtures"
GROOVY = FIXTURES / "gradle-multi-module-groovy"


@pytest.fixture
def project():
    return GradleAdapter().infer_structure(GROOVY)


def test_create_project_is_a_stub(project):
    with pytest.raises(NotImplementedError):
        GradleAdapter().create_project(None, Path("/tmp/x"))


def test_add_module_is_a_stub(project):
    with pytest.raises(NotImplementedError):
        GradleAdapter().add_module(project, None)


def test_remove_module_is_a_stub(project):
    with pytest.raises(NotImplementedError):
        GradleAdapter().remove_module(project, "core")


def test_update_dependency_is_a_stub(project):
    with pytest.raises(NotImplementedError):
        GradleAdapter().update_dependency(project, "core", None)


def test_remove_dependency_is_a_stub(project):
    with pytest.raises(NotImplementedError):
        GradleAdapter().remove_dependency(project, "com.example", "core")


def test_remove_direct_dependency_is_a_stub(project):
    with pytest.raises(NotImplementedError):
        GradleAdapter().remove_direct_dependency(project, "api", "com.example", "core")


def test_register_directory_role_is_a_stub(project):
    with pytest.raises(NotImplementedError):
        GradleAdapter().register_directory_role(
            project, "core", Path("src/main/proto"), "source"
        )


def test_unregister_directory_role_is_a_stub(project):
    with pytest.raises(NotImplementedError):
        GradleAdapter().unregister_directory_role(
            project, "core", Path("src/main/proto"), "source"
        )
