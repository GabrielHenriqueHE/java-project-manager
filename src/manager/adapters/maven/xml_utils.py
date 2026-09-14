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


def append_with_matching_indent(
    container: etree._Element, new_child: etree._Element
) -> None:
    """Anexa new_child como ultimo filho de container, reproduzindo o padrao de
    indentacao (tail/text) ja usado pelos filhos existentes, para nao deixar a
    nova entrada colada ou com indentacao diferente das demais.
    """
    existing_children = list(container)
    if not existing_children:
        opening_text = container.text or "\n"
        container.append(new_child)
        new_child.tail = opening_text
        return

    last = existing_children[-1]
    item_separator = (
        existing_children[0].tail
        if len(existing_children) > 1
        else (container.text or "\n")
    )
    closing_tail = last.tail
    container.append(new_child)
    new_child.tail = closing_tail
    last.tail = item_separator
