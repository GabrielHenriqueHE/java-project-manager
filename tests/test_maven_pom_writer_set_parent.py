from manager.adapters.maven.writer import MavenPomWriter


def test_set_parent_overwrites_existing_parent_block(tmp_path):
    pom_path = tmp_path / "core" / "pom.xml"
    MavenPomWriter().create_pom(
        pom_path,
        parent_group_id="com.example",
        parent_artifact_id="demo",
        parent_version="1.0.0",
        artifact_id="core",
    )

    MavenPomWriter().set_parent(
        pom_path,
        group_id="com.example",
        artifact_id="other-demo",
        version="2.0.0",
    )

    pom_text = pom_path.read_text()
    parent_block = pom_text.split("<parent>")[1].split("</parent>")[0]
    assert "<artifactId>other-demo</artifactId>" in parent_block
    assert "<version>2.0.0</version>" in parent_block
    assert pom_text.count("<parent>") == 1


def test_set_parent_creates_block_when_absent(tmp_path):
    pom_path = tmp_path / "demo" / "pom.xml"
    MavenPomWriter().create_pom(
        pom_path,
        artifact_id="demo",
        group_id="com.example",
        version="1.0.0",
        packaging="pom",
    )

    MavenPomWriter().set_parent(
        pom_path,
        group_id="com.example",
        artifact_id="aggregator",
        version="1.0.0",
    )

    pom_text = pom_path.read_text()
    assert "<parent>" in pom_text
    assert "<artifactId>aggregator</artifactId>" in pom_text
