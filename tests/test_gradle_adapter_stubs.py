from pathlib import Path

import pytest

from manager.adapters.gradle.adapter import GradleAdapter

FIXTURES = Path(__file__).parent / "fixtures"
GROOVY = FIXTURES / "gradle-multi-module-groovy"


@pytest.fixture
def project():
    return GradleAdapter().infer_structure(GROOVY)


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
