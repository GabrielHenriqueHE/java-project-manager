from pathlib import Path

from manager.adapters.gradle.parser import (
    find_build_file,
    find_settings_file,
    parse_build_file,
    parse_settings_file,
)

FIXTURES = Path(__file__).parent / "fixtures"
GROOVY = FIXTURES / "gradle-multi-module-groovy"
KOTLIN = FIXTURES / "gradle-multi-module-kotlin"


def test_find_build_file_prefers_kotlin_when_both_present(tmp_path):
    (tmp_path / "build.gradle").write_text("")
    (tmp_path / "build.gradle.kts").write_text("")

    assert find_build_file(tmp_path) == tmp_path / "build.gradle.kts"


def test_find_build_file_returns_none_when_absent(tmp_path):
    assert find_build_file(tmp_path) is None


def test_find_settings_file_returns_none_when_absent(tmp_path):
    assert find_settings_file(tmp_path) is None


def test_parse_settings_file_groovy():
    settings = parse_settings_file(GROOVY / "settings.gradle")

    assert settings.root_name == "multi-module-demo"
    assert settings.modules == [("bom", "bom"), ("core", "core"), ("api", "api")]


def test_parse_settings_file_kotlin():
    settings = parse_settings_file(KOTLIN / "settings.gradle.kts")

    assert settings.root_name == "multi-module-demo-kt"
    assert settings.modules == [("bom", "bom"), ("core", "core"), ("api", "api")]


def test_parse_settings_file_colon_path_and_shorthand_include(tmp_path):
    settings_path = tmp_path / "settings.gradle"
    settings_path.write_text(
        "include ':modules:core', 'api'\n"
        "include(\":extra\")\n"
    )

    settings = parse_settings_file(settings_path)

    assert settings.modules == [
        ("core", "modules/core"),
        ("api", "api"),
        ("extra", "extra"),
    ]


def test_parse_build_file_groovy_platform_module():
    parsed = parse_build_file(GROOVY / "bom" / "build.gradle")

    assert parsed.group_id == "com.example"
    assert parsed.version == "1.0.0"
    assert parsed.is_platform is True
    assert parsed.has_java_plugin is False
    assert parsed.dependencies == []
    coords = {(d.group_id, d.artifact_id, d.version) for d in parsed.managed_dependencies}
    assert coords == {
        ("org.apache.commons", "commons-lang3", "3.14.0"),
        ("com.example", "core", "1.0.0"),
    }
    assert all(dep.managed for dep in parsed.managed_dependencies)


def test_parse_build_file_kotlin_platform_module():
    parsed = parse_build_file(KOTLIN / "bom" / "build.gradle.kts")

    assert parsed.group_id == "com.example"
    assert parsed.version == "1.0.0"
    assert parsed.is_platform is True
    coords = {(d.group_id, d.artifact_id, d.version) for d in parsed.managed_dependencies}
    assert coords == {
        ("org.apache.commons", "commons-lang3", "3.14.0"),
        ("com.example", "core", "1.0.0"),
    }


def test_parse_build_file_groovy_java_library_module():
    parsed = parse_build_file(GROOVY / "core" / "build.gradle")

    assert parsed.has_java_plugin is True
    assert parsed.is_platform is False
    assert len(parsed.dependencies) == 1
    dep = parsed.dependencies[0]
    assert (dep.group_id, dep.artifact_id, dep.version) == (
        "org.junit.jupiter",
        "junit-jupiter",
        "5.10.0",
    )
    assert dep.scope == "test"
    assert dep.managed is False


def test_parse_build_file_kotlin_java_library_module():
    parsed = parse_build_file(KOTLIN / "core" / "build.gradle.kts")

    assert parsed.has_java_plugin is True
    dep = parsed.dependencies[0]
    assert (dep.group_id, dep.artifact_id, dep.version) == (
        "org.junit.jupiter",
        "junit-jupiter",
        "5.10.0",
    )
    assert dep.scope == "test"


def test_parse_build_file_external_platform_import_is_managed(tmp_path):
    build_file = tmp_path / "build.gradle"
    build_file.write_text(
        "plugins {\n"
        "    id 'java-library'\n"
        "}\n"
        "dependencies {\n"
        "    implementation platform('org.springframework.boot:spring-boot-dependencies:3.2.0')\n"
        "    implementation 'org.slf4j:slf4j-api:2.0.9'\n"
        "}\n"
    )

    parsed = parse_build_file(build_file)

    assert len(parsed.managed_dependencies) == 1
    managed = parsed.managed_dependencies[0]
    assert (managed.group_id, managed.artifact_id, managed.version) == (
        "org.springframework.boot",
        "spring-boot-dependencies",
        "3.2.0",
    )
    assert len(parsed.dependencies) == 1
    assert parsed.dependencies[0].artifact_id == "slf4j-api"


def test_parse_build_file_skips_project_references(tmp_path):
    build_file = tmp_path / "build.gradle"
    build_file.write_text(
        "dependencies {\n"
        "    implementation project(':core')\n"
        "    implementation 'com.example:real-dep:1.0.0'\n"
        "}\n"
    )

    parsed = parse_build_file(build_file)

    assert len(parsed.dependencies) == 1
    assert parsed.dependencies[0].artifact_id == "real-dep"


def test_parse_build_file_ignores_plugin_version_as_project_version(tmp_path):
    build_file = tmp_path / "build.gradle.kts"
    build_file.write_text(
        "plugins {\n"
        '    id("org.springframework.boot") version "3.2.0"\n'
        "}\n"
        'group = "com.example"\n'
        'version = "1.0.0"\n'
    )

    parsed = parse_build_file(build_file)

    assert parsed.version == "1.0.0"
    assert parsed.group_id == "com.example"


def test_parse_build_file_no_dependencies_block(tmp_path):
    build_file = tmp_path / "build.gradle"
    build_file.write_text("plugins {\n    id 'java-library'\n}\n")

    parsed = parse_build_file(build_file)

    assert parsed.dependencies == []
    assert parsed.managed_dependencies == []
