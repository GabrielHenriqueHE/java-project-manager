from lxml import etree


def namespace_of(root: etree._Element) -> str:
    """Retorna o prefixo de namespace (ex.: '{http://maven.apache.org/POM/4.0.0}') de um elemento raiz."""
    if root.tag.startswith("{"):
        uri = root.tag[1 : root.tag.index("}")]
        return f"{{{uri}}}"
    return ""


def remove_element_preserving_whitespace(elem: etree._Element) -> None:
    """Remove um elemento da arvore, empurrando seu 'tail' (texto/whitespace apos
    a tag de fechamento) para o irmao anterior (ou para o texto do pai), evitando
    deixar uma linha em branco no lugar do elemento removido.
    """
    parent = elem.getparent()
    if parent is None:
        return
    previous = elem.getprevious()
    if previous is not None:
        previous.tail = elem.tail
    else:
        parent.text = elem.tail
    parent.remove(elem)
