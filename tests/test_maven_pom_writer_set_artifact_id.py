from manager.adapters.maven.writer import MavenPomWriter


def test_set_artifact_id_overwrites_existing_value(tmp_path):
    pom_path = tmp_path / "core" / "pom.xml"
    MavenPomWriter().create_pom(
        pom_path,
        parent_group_id="com.example",
        parent_artifact_id="demo",
        parent_version="1.0.0",
        artifact_id="core",
    )

    MavenPomWriter().set_artifact_id(pom_path, "core-copy")

    pom_text = pom_path.read_text()
    assert "<artifactId>core-copy</artifactId>" in pom_text
    assert "<artifactId>core</artifactId>" not in pom_text
    # <parent> continua intacto - so o artifactId do proprio modulo muda
    assert "<artifactId>demo</artifactId>" in pom_text
