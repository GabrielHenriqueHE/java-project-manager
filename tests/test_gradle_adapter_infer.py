from pathlib import Path

import pytest

from manager.adapters.gradle.adapter import GradleAdapter
from manager.models import Module

FIXTURES = Path(__file__).parent / "fixtures"
GROOVY = FIXTURES / "gradle-multi-module-groovy"
KOTLIN = FIXTURES / "gradle-multi-module-kotlin"


def _flatten(module: Module) -> list[Module]:
    result = [module]
    for sub in module.submodules:
        result.extend(_flatten(sub))
    return result


def test_detect_recognizes_groovy_project():
    assert GradleAdapter().detect(GROOVY) is True


def test_detect_recognizes_kotlin_project():
    assert GradleAdapter().detect(KOTLIN) is True


def test_detect_rejects_non_gradle_dir(tmp_path):
    assert GradleAdapter().detect(tmp_path) is False


def test_detect_accepts_settings_only_root(tmp_path):
    (tmp_path / "settings.gradle").write_text("rootProject.name = 'x'\n")
    assert GradleAdapter().detect(tmp_path) is True


@pytest.mark.parametrize("root", [GROOVY, KOTLIN])
def test_infer_structure_builds_full_module_tree(root):
    project = GradleAdapter().infer_structure(root)

    assert project.build_tool == "gradle"
    names = {m.name for m in _flatten(project.root_module)}
    assert names == {project.root_module.name, "bom", "core", "api"}


def test_infer_structure_groovy_root_has_no_build_file_falls_back_to_settings():
    project = GradleAdapter().infer_structure(GROOVY)

    assert project.name == "multi-module-demo"
    assert project.root_module.metadata.packaging == "pom"
    assert project.root_module.metadata.group_id is None
    assert project.root_module.build_file.path == Path("settings.gradle")


def test_infer_structure_kotlin_root_has_own_build_file():
    project = GradleAdapter().infer_structure(KOTLIN)

    assert project.name == "multi-module-demo-kt"
    assert project.root_module.metadata.packaging == "pom"
    assert project.root_module.build_file.path == Path("build.gradle.kts")


@pytest.mark.parametrize("root", [GROOVY, KOTLIN])
def test_infer_structure_identifies_platform_module_as_bom(root):
    project = GradleAdapter().infer_structure(root)
    modules = {m.name: m for m in _flatten(project.root_module)}

    assert modules["bom"].is_bom is True
    assert modules["bom"].metadata.packaging == "pom"
    coords = {(d.group_id, d.artifact_id) for d in project.managed_dependencies}
    assert ("org.apache.commons", "commons-lang3") in coords
    assert ("com.example", "core") in coords


@pytest.mark.parametrize("root", [GROOVY, KOTLIN])
def test_infer_structure_java_library_module_metadata(root):
    project = GradleAdapter().infer_structure(root)
    modules = {m.name: m for m in _flatten(project.root_module)}

    core = modules["core"]
    assert core.metadata.packaging == "jar"
    assert core.metadata.group_id == "com.example"
    assert core.metadata.version == "1.0.0"
    assert core.is_bom is False


@pytest.mark.parametrize("root", [GROOVY, KOTLIN])
def test_infer_structure_direct_dependency_does_not_leak_into_managed(root):
    project = GradleAdapter().infer_structure(root)
    modules = {m.name: m for m in _flatten(project.root_module)}

    api = modules["api"]
    direct = [d for d in api.dependencies if not d.managed]
    assert any(d.artifact_id == "core" for d in direct)

    managed_names = {d.artifact_id for d in project.managed_dependencies}
    # "core" existe como direta em api e como gerenciada no bom -
    # sao entradas distintas, uma nao deve contaminar a outra.
    assert "core" in managed_names


@pytest.mark.parametrize("root", [GROOVY, KOTLIN])
def test_infer_structure_detects_standard_source_layout(root):
    project = GradleAdapter().infer_structure(root)
    modules = {m.name: m for m in _flatten(project.root_module)}

    core = modules["core"]
    assert core.directory_structure.convention == "maven-standard"
    assert core.directory_structure.source_dirs == ["src/main/java"]


def test_infer_structure_result_is_deterministic():
    adapter = GradleAdapter()
    first = adapter.infer_structure(GROOVY)
    second = adapter.infer_structure(GROOVY)

    assert first == second


def test_infer_structure_single_module_without_settings_file(tmp_path):
    (tmp_path / "build.gradle").write_text(
        "plugins {\n    id 'java-library'\n}\n"
        "group = 'com.example'\n"
        "version = '2.0.0'\n"
    )

    project = GradleAdapter().infer_structure(tmp_path)

    assert project.root_module.name == tmp_path.name
    assert project.root_module.metadata.group_id == "com.example"
    assert project.root_module.metadata.packaging == "jar"
    assert project.root_module.submodules == []


def test_infer_structure_rejects_included_module_without_build_file(tmp_path):
    (tmp_path / "settings.gradle").write_text("include 'missing'\n")
    (tmp_path / "missing").mkdir()

    with pytest.raises(ValueError, match="nao tem build.gradle"):
        GradleAdapter().infer_structure(tmp_path)
