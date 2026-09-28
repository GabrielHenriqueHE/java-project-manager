from manager.adapters.common.copy import copy_module_tree


def test_copy_module_tree_copies_files_recursively(tmp_path):
    source = tmp_path / "source"
    (source / "src" / "main" / "java").mkdir(parents=True)
    (source / "src" / "main" / "java" / "Foo.java").write_text("class Foo {}")
    (source / "pom.xml").write_text("<project/>")

    dest = tmp_path / "dest"
    copy_module_tree(source, dest)

    assert (dest / "pom.xml").read_text() == "<project/>"
    assert (dest / "src" / "main" / "java" / "Foo.java").read_text() == "class Foo {}"


def test_copy_module_tree_ignores_known_build_output_dirs(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "pom.xml").write_text("<project/>")
    for ignored in ("target", "build", "bin", ".gradle", "out", ".git", ".idea"):
        (source / ignored).mkdir()
        (source / ignored / "marker").write_text("should not be copied")

    dest = tmp_path / "dest"
    copy_module_tree(source, dest)

    assert (dest / "pom.xml").is_file()
    for ignored in ("target", "build", "bin", ".gradle", "out", ".git", ".idea"):
        assert not (dest / ignored).exists()
