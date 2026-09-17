import pytest

from manager.adapters.gradle.adapter import GradleAdapter
from manager.manifest import ModuleManifest
from manager.models import Dependency, DirectoryStructure, Module, ProjectMetadata


def _flatten(module: Module) -> list[Module]:
    result = [module]
    for sub in module.submodules:
        result.extend(_flatten(sub))
    return result


def test_create_project_materializes_single_module(tmp_path):
    destination = tmp_path / "demo"
    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo", group_id="com.example", version="1.0.0"
        )
    )

    project = GradleAdapter().create_project(manifest, destination)

    assert project.root_module.name == "demo"
    assert project.root_module.metadata.group_id == "com.example"
    assert project.root_module.metadata.version == "1.0.0"
    assert (destination / "build.gradle").is_file()
    assert (destination / "settings.gradle").is_file()


def test_create_project_materializes_multi_module(tmp_path):
    destination = tmp_path / "demo"
    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo",
            group_id="com.example",
            version="1.0.0",
            packaging="pom",
        ),
        submodules=[
            ModuleManifest(
                metadata=ProjectMetadata(
                    artifact_id="core", group_id="com.example", version="1.0.0"
                )
            ),
            ModuleManifest(
                metadata=ProjectMetadata(
                    artifact_id="api",
                    group_id="com.example",
                    version="2.0.0",
                )
            ),
        ],
    )

    project = GradleAdapter().create_project(manifest, destination)
    modules = {m.name: m for m in _flatten(project.root_module)}

    assert set(modules) == {"demo", "core", "api"}
    assert modules["core"].metadata.version == "1.0.0"
    assert modules["api"].metadata.version == "2.0.0"
    settings_text = (destination / "settings.gradle").read_text()
    assert "'core'" in settings_text
    assert "'api'" in settings_text


def test_create_project_materializes_bom_module(tmp_path):
    destination = tmp_path / "demo"
    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo",
            group_id="com.example",
            version="1.0.0",
            packaging="pom",
        ),
        submodules=[
            ModuleManifest(
                metadata=ProjectMetadata(
                    artifact_id="demo-bom",
                    group_id="com.example",
                    version="1.0.0",
                    packaging="pom",
                ),
                dependencies=[
                    Dependency(
                        group_id="org.apache.commons",
                        artifact_id="commons-lang3",
                        version="3.14.0",
                        managed=True,
                    )
                ],
            ),
            ModuleManifest(
                metadata=ProjectMetadata(
                    artifact_id="core", group_id="com.example", version="1.0.0"
                ),
                dependencies=[
                    Dependency(
                        group_id="org.apache.commons",
                        artifact_id="commons-lang3",
                        managed=False,
                    )
                ],
            ),
        ],
    )

    project = GradleAdapter().create_project(manifest, destination)
    modules = {m.name: m for m in _flatten(project.root_module)}

    assert modules["demo-bom"].is_bom is True
    managed = {d.artifact_id: d for d in project.managed_dependencies}
    assert managed["commons-lang3"].version == "3.14.0"

    core_deps = {d.artifact_id: d for d in modules["core"].dependencies}
    assert core_deps["commons-lang3"].managed is False
    build_text = (destination / "demo-bom" / "build.gradle").read_text()
    assert "java-platform" in build_text


def test_create_project_creates_directories(tmp_path):
    destination = tmp_path / "demo"
    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo", group_id="com.example", version="1.0.0"
        ),
        directory_structure=DirectoryStructure(
            source_dirs=["src/main/java"],
            test_dirs=[],
            resource_dirs=[],
            test_resource_dirs=[],
        ),
    )

    GradleAdapter().create_project(manifest, destination)

    assert (destination / "src" / "main" / "java").is_dir()


def test_create_project_rejects_duplicate_module_names(tmp_path):
    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo",
            group_id="com.example",
            version="1.0.0",
            packaging="pom",
        ),
        submodules=[
            ModuleManifest(metadata=ProjectMetadata(artifact_id="core")),
            ModuleManifest(metadata=ProjectMetadata(artifact_id="core")),
        ],
    )

    with pytest.raises(ValueError, match="duplicado"):
        GradleAdapter().create_project(manifest, tmp_path / "demo")

    assert not (tmp_path / "demo").exists()


def test_create_project_rejects_managed_dependency_without_version(tmp_path):
    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo",
            group_id="com.example",
            version="1.0.0",
            packaging="pom",
        ),
        dependencies=[
            Dependency(
                group_id="org.apache.commons", artifact_id="commons-lang3", managed=True
            )
        ],
    )

    with pytest.raises(ValueError, match="precisa de version"):
        GradleAdapter().create_project(manifest, tmp_path / "demo")

    assert not (tmp_path / "demo").exists()


def test_create_project_rejects_submodule_holder_with_non_pom_packaging(tmp_path):
    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo",
            group_id="com.example",
            version="1.0.0",
            packaging="jar",
        ),
        submodules=[ModuleManifest(metadata=ProjectMetadata(artifact_id="core"))],
    )

    with pytest.raises(ValueError, match="packaging precisa ser 'pom'"):
        GradleAdapter().create_project(manifest, tmp_path / "demo")

    assert not (tmp_path / "demo").exists()


def test_create_project_allows_root_without_group_id_or_version(tmp_path):
    # Diferente do Maven: o Gradle nao tem <parent> de quem herdar, entao
    # group/version ausentes na raiz nao sao um erro - so ficam de fora do
    # build.gradle.
    manifest = ModuleManifest(metadata=ProjectMetadata(artifact_id="demo"))

    project = GradleAdapter().create_project(manifest, tmp_path / "demo")

    assert project.root_module.name == "demo"
    assert project.root_module.metadata.group_id is None


def test_create_project_rejects_existing_nonempty_destination(tmp_path):
    destination = tmp_path / "demo"
    destination.mkdir()
    (destination / "README.md").write_text("ja tem algo aqui")
    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo", group_id="com.example", version="1.0.0"
        )
    )

    with pytest.raises(ValueError, match="ja existe e nao esta vazio"):
        GradleAdapter().create_project(manifest, destination)

    assert not (destination / "build.gradle").exists()


def test_create_project_allows_existing_empty_destination(tmp_path):
    destination = tmp_path / "demo"
    destination.mkdir()
    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo", group_id="com.example", version="1.0.0"
        )
    )

    project = GradleAdapter().create_project(manifest, destination)

    assert project.root_module.name == "demo"


def test_create_project_with_source_root_copies_real_files(tmp_path):
    source_root = tmp_path / "snapshot"
    java_dir = source_root / "core" / "src" / "main" / "java" / "com" / "example"
    java_dir.mkdir(parents=True)
    (java_dir / "Core.java").write_text("package com.example;\nclass Core {}\n")

    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo",
            group_id="com.example",
            version="1.0.0",
            packaging="pom",
        ),
        submodules=[
            ModuleManifest(
                metadata=ProjectMetadata(artifact_id="core"),
                directory_structure=DirectoryStructure(
                    source_dirs=["src/main/java"],
                    test_dirs=[],
                    resource_dirs=[],
                    test_resource_dirs=[],
                ),
            ),
        ],
    )

    project = GradleAdapter().create_project(
        manifest, tmp_path / "created", source_root=source_root
    )

    copied = (
        tmp_path
        / "created"
        / "core"
        / "src"
        / "main"
        / "java"
        / "com"
        / "example"
        / "Core.java"
    )
    assert copied.is_file()
    assert copied.read_text() == "package com.example;\nclass Core {}\n"
    assert project.root_module.name == "demo"


def test_create_project_without_matching_snapshot_falls_back_to_mkdir(tmp_path):
    source_root = tmp_path / "snapshot"
    source_root.mkdir()  # existe, mas sem subpasta para "core"

    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo", group_id="com.example", version="1.0.0", packaging="pom"
        ),
        submodules=[ModuleManifest(metadata=ProjectMetadata(artifact_id="core"))],
    )

    project = GradleAdapter().create_project(
        manifest, tmp_path / "created", source_root=source_root
    )

    core = next(m for m in _flatten(project.root_module) if m.name == "core")
    assert (tmp_path / "created" / "core" / "src" / "main" / "java").is_dir()
    assert core.directory_structure.source_dirs == ["src/main/java"]


def test_create_project_result_matches_fresh_inference(tmp_path):
    destination = tmp_path / "demo"
    manifest = ModuleManifest(
        metadata=ProjectMetadata(
            artifact_id="demo",
            group_id="com.example",
            version="1.0.0",
            packaging="pom",
        ),
        submodules=[ModuleManifest(metadata=ProjectMetadata(artifact_id="core"))],
    )

    project = GradleAdapter().create_project(manifest, destination)
    reinferred = GradleAdapter().infer_structure(destination)

    assert project == reinferred
