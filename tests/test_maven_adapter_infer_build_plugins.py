import shutil
from pathlib import Path

from manager.adapters.maven.adapter import MavenAdapter

FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "maven-multi-module"


def _project_root(tmp_path) -> Path:
    dest = tmp_path / "project"
    shutil.copytree(FIXTURE_SOURCE, dest)
    return dest


def test_infer_structure_reflects_registered_source_directory(tmp_path):
    project_root = _project_root(tmp_path)
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)

    project = adapter.register_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )

    core = next(m for m in _flatten(project.root_module) if m.name == "core")
    assert "src/main/proto" in core.directory_structure.source_dirs


def test_infer_structure_reflects_registered_resource_directory(tmp_path):
    project_root = _project_root(tmp_path)
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "extra-resources").mkdir(parents=True)

    project = adapter.register_directory_role(
        project, "core", Path("src/main/extra-resources"), "resource"
    )

    core = next(m for m in _flatten(project.root_module) if m.name == "core")
    assert "src/main/extra-resources" in core.directory_structure.resource_dirs


def test_infer_structure_reflects_registered_test_source_and_test_resource(tmp_path):
    project_root = _project_root(tmp_path)
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "test" / "proto").mkdir(parents=True)
    (project_root / "core" / "src" / "test" / "extra-resources").mkdir(parents=True)

    project = adapter.register_directory_role(
        project, "core", Path("src/test/proto"), "test-source"
    )
    project = adapter.register_directory_role(
        project, "core", Path("src/test/extra-resources"), "test-resource"
    )

    core = next(m for m in _flatten(project.root_module) if m.name == "core")
    assert "src/test/proto" in core.directory_structure.test_dirs
    assert "src/test/extra-resources" in core.directory_structure.test_resource_dirs


def test_infer_structure_ignores_registered_directory_removed_from_disk(tmp_path):
    project_root = _project_root(tmp_path)
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    proto_dir = project_root / "core" / "src" / "main" / "proto"
    proto_dir.mkdir(parents=True)

    project = adapter.register_directory_role(
        project, "core", Path("src/main/proto"), "source"
    )
    proto_dir.rmdir()

    project = adapter.infer_structure(project_root)
    core = next(m for m in _flatten(project.root_module) if m.name == "core")
    assert "src/main/proto" not in core.directory_structure.source_dirs


def test_infer_structure_without_build_helper_plugin_is_unaffected():
    project = MavenAdapter().infer_structure(FIXTURE_SOURCE)
    core = next(m for m in _flatten(project.root_module) if m.name == "core")

    assert core.directory_structure.source_dirs == ["src/main/java"]


def test_infer_structure_does_not_duplicate_already_standard_directory(tmp_path):
    project_root = _project_root(tmp_path)
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)

    project = adapter.register_directory_role(
        project, "core", Path("src/main/java"), "source"
    )

    core = next(m for m in _flatten(project.root_module) if m.name == "core")
    assert core.directory_structure.source_dirs == ["src/main/java"]


def test_infer_structure_ignores_unrelated_plugin(tmp_path):
    project_root = _project_root(tmp_path)
    core_pom = project_root / "core" / "pom.xml"
    core_pom.write_text(
        core_pom.read_text().replace(
            "</dependencies>\n</project>",
            "</dependencies>\n"
            "  <build>\n"
            "    <plugins>\n"
            "      <plugin>\n"
            "        <groupId>org.apache.maven.plugins</groupId>\n"
            "        <artifactId>maven-compiler-plugin</artifactId>\n"
            "        <executions>\n"
            "          <execution>\n"
            "            <id>default-compile</id>\n"
            "            <goals>\n"
            "              <goal>compile</goal>\n"
            "            </goals>\n"
            "          </execution>\n"
            "        </executions>\n"
            "      </plugin>\n"
            "    </plugins>\n"
            "  </build>\n"
            "</project>",
        )
    )

    project = MavenAdapter().infer_structure(project_root)

    core = next(m for m in _flatten(project.root_module) if m.name == "core")
    assert core.directory_structure.source_dirs == ["src/main/java"]


def test_infer_structure_is_deterministic_with_registered_directories(tmp_path):
    project_root = _project_root(tmp_path)
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)
    adapter.register_directory_role(project, "core", Path("src/main/proto"), "source")

    assert adapter.infer_structure(project_root) == adapter.infer_structure(
        project_root
    )


def test_infer_structure_does_not_mutate_versioned_fixture(tmp_path):
    project_root = _project_root(tmp_path)
    adapter = MavenAdapter()
    project = adapter.infer_structure(project_root)
    (project_root / "core" / "src" / "main" / "proto").mkdir(parents=True)

    adapter.register_directory_role(project, "core", Path("src/main/proto"), "source")

    fixture_pom = (FIXTURE_SOURCE / "core" / "pom.xml").read_text()
    assert "build-helper-maven-plugin" not in fixture_pom


def _flatten(module):
    result = [module]
    for sub in module.submodules:
        result.extend(_flatten(sub))
    return result
