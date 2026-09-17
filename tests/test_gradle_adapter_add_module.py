import shutil
from pathlib import Path

import pytest

from manager.adapters.gradle.adapter import GradleAdapter
from manager.models import BuildFile, Dependency, Module, ProjectMetadata

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


def _draft(artifact_id: str, **metadata_overrides) -> Module:
    return Module(
        name=artifact_id,
        relative_path=Path(artifact_id),
        metadata=ProjectMetadata(artifact_id=artifact_id, **metadata_overrides),
        build_file=BuildFile(path=Path(artifact_id) / "build.gradle"),
    )


def _module_names(project) -> set[str]:
    return {m.name for m in [project.root_module, *project.root_module.submodules]}


@pytest.mark.parametrize("root_fixture", ["groovy_root", "kotlin_root"])
def test_add_module_creates_build_file_include_and_directories(root_fixture, request):
    project_root = request.getfixturevalue(root_fixture)
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.add_module(project, _draft("utils"))

    assert "utils" in _module_names(updated)
    assert (project_root / "utils" / "src" / "main" / "java").is_dir()
    assert (project_root / "utils" / "src" / "test" / "java").is_dir()


def test_add_module_uses_groovy_build_file_for_groovy_project(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    adapter.add_module(project, _draft("utils"))

    assert (groovy_root / "utils" / "build.gradle").is_file()
    assert not (groovy_root / "utils" / "build.gradle.kts").exists()
    settings_text = (groovy_root / "settings.gradle").read_text()
    assert "'utils'" in settings_text


def test_add_module_uses_kotlin_build_file_for_kotlin_project(kotlin_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(kotlin_root)

    adapter.add_module(project, _draft("utils"))

    assert (kotlin_root / "utils" / "build.gradle.kts").is_file()
    settings_text = (kotlin_root / "settings.gradle.kts").read_text()
    assert '"utils"' in settings_text


def test_add_module_writes_packaging_and_metadata(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.add_module(
        project, _draft("utils", group_id="com.other", version="9.9.9")
    )
    utils = next(m for m in updated.root_module.submodules if m.name == "utils")

    assert utils.metadata.group_id == "com.other"
    assert utils.metadata.version == "9.9.9"
    assert utils.metadata.packaging == "jar"


def test_add_module_writes_initial_dependencies(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    module = Module(
        name="utils",
        relative_path=Path("utils"),
        metadata=ProjectMetadata(artifact_id="utils", packaging="pom"),
        build_file=BuildFile(path=Path("utils") / "build.gradle"),
        dependencies=[
            Dependency(
                group_id="org.apache.commons",
                artifact_id="commons-lang3",
                version="3.14.0",
                managed=True,
            )
        ],
    )

    updated = adapter.add_module(project, module)
    utils = next(m for m in updated.root_module.submodules if m.name == "utils")

    assert any(dep.artifact_id == "commons-lang3" for dep in utils.dependencies)


def test_add_module_rejects_non_root_parent(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="raiz"):
        adapter.add_module(project, _draft("novo"), parent_name="core")


def test_add_module_accepts_explicit_root_as_parent(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.add_module(
        project, _draft("utils"), parent_name=project.root_module.name
    )

    assert "utils" in _module_names(updated)


def test_add_module_rejects_duplicate_name(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="Ja existe"):
        adapter.add_module(project, _draft("core"))


def test_add_module_rejects_unknown_parent(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.add_module(project, _draft("novo"), parent_name="inexistente")


def test_add_module_rejects_existing_directory(groovy_root):
    (groovy_root / "assets").mkdir()

    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="ja existe"):
        adapter.add_module(project, _draft("assets"))


def test_add_module_result_matches_fresh_inference(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.add_module(project, _draft("utils"))
    reinferred = adapter.infer_structure(groovy_root)

    assert _module_names(reinferred) == _module_names(updated)
