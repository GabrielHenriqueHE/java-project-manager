from pathlib import Path

import pytest

from manager.adapters.maven.adapter import MavenAdapter
from manager.models import Module

FIXTURES = Path(__file__).parent / "fixtures"
MULTI_MODULE = FIXTURES / "maven-multi-module"
MALFORMED = FIXTURES / "malformed-pom"


def _flatten(module: Module) -> list[Module]:
    result = [module]
    for sub in module.submodules:
        result.extend(_flatten(sub))
    return result


def test_detect_recognizes_maven_project():
    assert MavenAdapter().detect(MULTI_MODULE) is True


def test_detect_rejects_non_maven_dir(tmp_path):
    assert MavenAdapter().detect(tmp_path) is False


def test_infer_structure_builds_full_module_tree():
    project = MavenAdapter().infer_structure(MULTI_MODULE)

    assert project.build_tool == "maven"
    names = {m.name for m in _flatten(project.root_module)}
    assert names == {"multi-module-demo", "multi-module-demo-bom", "core", "api"}


def test_infer_structure_identifies_bom_module():
    project = MavenAdapter().infer_structure(MULTI_MODULE)
    modules = {m.name: m for m in _flatten(project.root_module)}

    assert modules["multi-module-demo-bom"].is_bom is True
    assert modules["core"].is_bom is False
    assert modules["multi-module-demo"].is_bom is False


def test_infer_structure_resolves_managed_dependencies():
    project = MavenAdapter().infer_structure(MULTI_MODULE)

    managed = {d.artifact_id: d for d in project.managed_dependencies}
    assert managed["commons-lang3"].version == "3.14.0"
    assert managed["commons-lang3"].managed is True
    assert managed["core"].version == "1.0.0"


def test_infer_structure_resolves_inter_module_dependency():
    project = MavenAdapter().infer_structure(MULTI_MODULE)
    modules = {m.name: m for m in _flatten(project.root_module)}

    api_deps = {d.artifact_id: d for d in modules["api"].dependencies}
    assert api_deps["core"].group_id == "com.example"
    assert api_deps["core"].managed is False


def test_infer_structure_detects_maven_standard_directory_layout():
    project = MavenAdapter().infer_structure(MULTI_MODULE)
    modules = {m.name: m for m in _flatten(project.root_module)}

    core_dirs = modules["core"].directory_structure
    assert core_dirs.convention == "maven-standard"
    assert core_dirs.source_dirs == ["src/main/java"]

    bom_dirs = modules["multi-module-demo-bom"].directory_structure
    assert bom_dirs.source_dirs == []


def test_infer_structure_is_deterministic():
    adapter = MavenAdapter()
    assert adapter.infer_structure(MULTI_MODULE) == adapter.infer_structure(
        MULTI_MODULE
    )


def test_infer_structure_raises_for_missing_pom(tmp_path):
    with pytest.raises(FileNotFoundError):
        MavenAdapter().infer_structure(tmp_path)


def test_infer_structure_raises_clear_error_for_malformed_pom():
    with pytest.raises(ValueError, match="pom.xml invalido"):
        MavenAdapter().infer_structure(MALFORMED)


@pytest.mark.parametrize(
    "method_name",
    ["add_module", "update_dependency", "update_metadata"],
)
def test_mutation_methods_are_not_implemented_yet(method_name):
    adapter = MavenAdapter()
    method = getattr(adapter, method_name)
    with pytest.raises(NotImplementedError):
        if method_name == "add_module":
            method(None, None)
        else:
            method(None, None, None)
