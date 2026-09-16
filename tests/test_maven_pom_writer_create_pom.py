from manager.adapters.maven.writer import MavenPomWriter


def test_create_pom_with_parent_writes_parent_block(tmp_path):
    pom_path = tmp_path / "core" / "pom.xml"
    MavenPomWriter().create_pom(
        pom_path,
        parent_group_id="com.example",
        parent_artifact_id="demo",
        parent_version="1.0.0",
        artifact_id="core",
    )

    pom_text = pom_path.read_text()
    assert "<parent>" in pom_text
    assert "<groupId>com.example</groupId>" in pom_text
    assert "<artifactId>demo</artifactId>" in pom_text
    assert "<artifactId>core</artifactId>" in pom_text


def test_create_pom_without_parent_omits_parent_block(tmp_path):
    pom_path = tmp_path / "demo" / "pom.xml"
    MavenPomWriter().create_pom(
        pom_path,
        artifact_id="demo",
        group_id="com.example",
        version="1.0.0",
        packaging="pom",
    )

    pom_text = pom_path.read_text()
    assert "<parent>" not in pom_text
    assert "<groupId>com.example</groupId>" in pom_text
    assert "<version>1.0.0</version>" in pom_text
    assert "<artifactId>demo</artifactId>" in pom_text


def test_create_pom_with_submodule_names_writes_modules_section(tmp_path):
    pom_path = tmp_path / "demo" / "pom.xml"
    MavenPomWriter().create_pom(
        pom_path,
        artifact_id="demo",
        group_id="com.example",
        version="1.0.0",
        packaging="pom",
        submodule_names=["core", "api"],
    )

    pom_text = pom_path.read_text()
    assert "<modules>" in pom_text
    assert "<module>core</module>" in pom_text
    assert "<module>api</module>" in pom_text
    # <modules> vem depois de <packaging> e antes de fechar </project>
    assert pom_text.index("<modules>") > pom_text.index("<packaging>")


def test_create_pom_without_submodule_names_omits_modules_section(tmp_path):
    pom_path = tmp_path / "core" / "pom.xml"
    MavenPomWriter().create_pom(
        pom_path,
        parent_group_id="com.example",
        parent_artifact_id="demo",
        parent_version="1.0.0",
        artifact_id="core",
    )

    assert "<modules>" not in pom_path.read_text()
