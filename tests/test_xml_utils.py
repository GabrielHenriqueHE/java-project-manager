from lxml import etree

from manager.adapters.maven.xml_utils import append_with_matching_indent


def test_append_with_matching_indent_indents_first_child_of_empty_container():
    root = etree.fromstring("<root><a><b/></a></root>")
    a = root.find("a")
    b = a.find("b")

    new_child = etree.Element("c")
    append_with_matching_indent(b, new_child)

    xml = etree.tostring(root).decode()
    assert "<b>\n      <c/>\n    </b>" in xml


def test_append_with_matching_indent_nests_correctly_multiple_levels_deep():
    root = etree.fromstring("<root/>")

    level1 = etree.Element("level1")
    append_with_matching_indent(root, level1)
    level2 = etree.Element("level2")
    append_with_matching_indent(level1, level2)
    level3 = etree.Element("level3")
    append_with_matching_indent(level2, level3)

    xml = etree.tostring(root).decode()
    assert (
        "<root>\n  <level1>\n    <level2>\n      <level3/>\n    </level2>\n  </level1>\n</root>"
        == xml
    )
