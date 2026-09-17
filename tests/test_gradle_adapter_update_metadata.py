import shutil
from pathlib import Path

import pytest

from manager.adapters.gradle.adapter import GradleAdapter
from manager.models import ProjectMetadata

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


def _metadata(artifact_id: str, **overrides) -> ProjectMetadata:
    overrides.setdefault("packaging", "jar")
    return ProjectMetadata(artifact_id=artifact_id, **overrides)


def _find(project, name):
    def walk(module):
        if module.name == name:
            return module
        for sub in module.submodules:
            found = walk(sub)
            if found is not None:
                return found
        return None

    return walk(project.root_module)


@pytest.mark.parametrize("root_fixture", ["groovy_root", "kotlin_root"])
def test_update_metadata_sets_group_and_version(root_fixture, request):
    project_root = request.getfixturevalue(root_fixture)
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)

    updated = adapter.update_metadata(
        project, "core", _metadata("core", group_id="com.other", version="2.0.0")
    )
    core = _find(updated, "core")

    assert core.metadata.group_id == "com.other"
    assert core.metadata.version == "2.0.0"


@pytest.mark.parametrize("root_fixture", ["groovy_root", "kotlin_root"])
def test_update_metadata_clears_group_and_version(root_fixture, request):
    project_root = request.getfixturevalue(root_fixture)
    adapter = GradleAdapter()
    project = adapter.infer_structure(project_root)
    core = _find(project, "core")
    assert core.metadata.group_id == "com.example"

    updated = adapter.update_metadata(
        project, "core", _metadata("core", group_id=None, version=None)
    )
    core = _find(updated, "core")

    assert core.metadata.group_id is None
    assert core.metadata.version is None


def test_update_metadata_rejects_artifact_id_rename(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="artifactId"):
        adapter.update_metadata(project, "core", _metadata("core-renamed"))


def test_update_metadata_rejects_packaging_change_on_bom_module(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="packaging"):
        adapter.update_metadata(project, "bom", _metadata("bom", packaging="jar"))


def test_update_metadata_rejects_packaging_change_when_module_has_submodules(
    groovy_root,
):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="packaging"):
        adapter.update_metadata(
            project,
            "multi-module-demo",
            _metadata("multi-module-demo", packaging="jar"),
        )


def test_update_metadata_swaps_packaging_jar_to_pom(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.update_metadata(
        project, "core", _metadata("core", packaging="pom")
    )
    core = _find(updated, "core")

    assert core.metadata.packaging == "pom"
    build_text = (groovy_root / "core" / "build.gradle").read_text()
    assert "java-platform" in build_text
    assert "java-library" not in build_text


def test_update_metadata_swaps_packaging_pom_to_jar(tmp_path):
    # Aggregator puro (sem plugins) - packaging "pom" sem ser BOM nem ter
    # submodulos, unico jeito de testar essa troca sem esbarrar no guard
    # de packaging/BOM/submodulos (as fixtures compartilhadas nao tem um
    # modulo folha nesse estado: "bom" e BOM, a raiz tem submodulos).
    (tmp_path / "settings.gradle").write_text(
        "rootProject.name = 'demo'\ninclude 'leaf'\n"
    )
    leaf_dir = tmp_path / "leaf"
    leaf_dir.mkdir()
    (leaf_dir / "build.gradle").write_text("group = 'com.example'\nversion = '1.0.0'\n")

    adapter = GradleAdapter()
    project = adapter.infer_structure(tmp_path)
    leaf = _find(project, "leaf")
    assert leaf.metadata.packaging == "pom"
    assert not leaf.is_bom

    updated = adapter.update_metadata(
        project, "leaf", _metadata("leaf", packaging="jar")
    )
    leaf = _find(updated, "leaf")

    assert leaf.metadata.packaging == "jar"
    build_text = (leaf_dir / "build.gradle").read_text()
    assert "java-platform" not in build_text
    assert "java" in build_text


def test_update_metadata_unchanged_packaging_does_not_touch_plugins(kotlin_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(kotlin_root)

    before = (kotlin_root / "build.gradle.kts").read_text()
    adapter.update_metadata(
        project,
        "multi-module-demo-kt",
        _metadata("multi-module-demo-kt", group_id="com.example", packaging="pom"),
    )
    after = (kotlin_root / "build.gradle.kts").read_text()

    assert "java-platform" not in after
    assert after != before  # group foi escrito
    assert "// aggregador puro" in after


def test_update_metadata_rejects_module_without_build_file(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="build.gradle"):
        adapter.update_metadata(
            project,
            "multi-module-demo",
            _metadata(
                "multi-module-demo",
                group_id="com.example",
                version="1.0.0",
                packaging="pom",
            ),
        )


def test_update_metadata_result_matches_fresh_inference(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    updated = adapter.update_metadata(
        project, "core", _metadata("core", version="9.9.9")
    )
    reinferred = adapter.infer_structure(groovy_root)

    assert updated == reinferred


def test_update_metadata_rejects_unknown_module(groovy_root):
    adapter = GradleAdapter()
    project = adapter.infer_structure(groovy_root)

    with pytest.raises(ValueError, match="nao encontrado"):
        adapter.update_metadata(project, "inexistente", _metadata("inexistente"))
