import shutil
from pathlib import Path

import pytest

from manager.adapters.maven.adapter import MavenAdapter
from manager.models import BuildFile, Dependency, Module, ProjectMetadata

FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "maven-multi-module"


@pytest.fixture
def project_root(tmp_path) -> Path:
    dest = tmp_path / "project"
    shutil.copytree(FIXTURE_SOURCE, dest)
    return dest


def _draft(artifact_id: str, **metadata_overrides) -> Module:
    return Module(
        name=artifact_id,
        relative_path=Path(artifact_id),
        metadata=ProjectMetadata(artifact_id=artifact_id, **metadata_overrides),
        build_file=BuildFile(path=Path(artifact_id) / "pom.xml"),
    )


def _module_names(project) -> set[str]:
    return {m.name for m in [project.root_module, *project.root_module.submodules]}


def test_add_module_registers_in_parent_pom_and_creates_directories(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.add_module(project, _draft("utils", name="Utils"))

    assert "utils" in _module_names(updated)
    assert (project_root / "pom.xml").read_text().count("<module>utils</module>") == 1
    assert (project_root / "utils" / "src" / "main" / "java").is_dir()
    assert (project_root / "utils" / "src" / "test" / "java").is_dir()


def test_add_module_inherits_group_id_and_version_from_parent(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.add_module(project, _draft("utils"))
    utils = next(m for m in updated.root_module.submodules if m.name == "utils")

    assert utils.metadata.group_id == "com.example"
    assert utils.metadata.version == "1.0.0"
    pom_text = (project_root / "utils" / "pom.xml").read_text()
    assert "<groupId>com.example</groupId>" not in pom_text.split("</parent>")[1]
    assert "<version>1.0.0</version>" not in pom_text.split("</parent>")[1]


def test_add_module_writes_explicit_group_id_when_it_differs_from_parent(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.add_module(
        project, _draft("utils", group_id="com.other", version="9.9.9")
    )
    utils = next(m for m in updated.root_module.submodules if m.name == "utils")

    assert utils.metadata.group_id == "com.other"
    assert utils.metadata.version == "9.9.9"


def test_add_module_writes_initial_dependencies(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    module = Module(
        name="utils",
        relative_path=Path("utils"),
        metadata=ProjectMetadata(artifact_id="utils"),
        build_file=BuildFile(path=Path("utils") / "pom.xml"),
        dependencies=[
            Dependency(
                group_id="org.apache.commons",
                artifact_id="commons-lang3",
                version="3.14.0",
            )
        ],
    )

    updated = adapter.add_module(project, module)
    utils = next(m for m in updated.root_module.submodules if m.name == "utils")

    assert any(dep.artifact_id == "commons-lang3" for dep in utils.dependencies)


def test_add_module_under_named_parent(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    # bom tem packaging=pom, entao pode receber submodulos mesmo sem <modules>
    # previo -- mas nosso escopo atual exige <modules> ja existente no pai.
    with pytest.raises(ValueError, match="modules"):
        adapter.add_module(
            project, _draft("sub-bom"), parent_name="multi-module-demo-bom"
        )


def test_add_module_rejects_duplicate_name(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="Ja existe"):
        adapter.add_module(project, _draft("core"))


def test_add_module_rejects_non_pom_parent(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="packaging"):
        adapter.add_module(project, _draft("novo"), parent_name="core")


def test_add_module_rejects_unknown_parent(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.add_module(project, _draft("novo"), parent_name="inexistente")


def test_add_module_rejects_existing_directory(project_root):
    # Diretorio orfao: existe em disco mas nao esta registrado como modulo em
    # nenhum pom, entao a checagem de nome duplicado nao pega este caso.
    (project_root / "assets").mkdir()

    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    with pytest.raises(ValueError, match="ja existe"):
        adapter.add_module(project, _draft("assets"))


def test_add_module_result_matches_fresh_inference(project_root):
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.add_module(project, _draft("utils"))
    reinferred = adapter.infer_structure(project_root)

    assert _module_names(reinferred) == _module_names(updated)
