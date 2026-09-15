from lxml import etree

POM_ELEMENT_ORDER = [
    "modelVersion",
    "parent",
    "groupId",
    "artifactId",
    "version",
    "packaging",
    "name",
    "description",
    "properties",
    "dependencyManagement",
    "dependencies",
    "modules",
    "build",
]


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
        # container esta vazio (sem filhos ainda, ex.: <plugins> recem-criado
        # por ensure_child_in_order): container.text e container.tail nao tem
        # nenhum padrao de indentacao existente para copiar, entao calculamos
        # a indentacao pela profundidade real de container na arvore (contar
        # ancestrais), em vez de assumir "\n" sem espacos - senao o filho fica
        # colado na tag de abertura (ex.: "<build><plugins>").
        depth = sum(1 for _ in container.iterancestors()) + 1
        container.text = "\n" + "  " * depth
        container.append(new_child)
        new_child.tail = "\n" + "  " * (depth - 1)
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


def ensure_child_in_order(
    container: etree._Element,
    tag: str,
    ns: str,
    order: list[str] = POM_ELEMENT_ORDER,
) -> etree._Element:
    """Retorna o filho <tag> de container, criando-o se necessario.

    Ao criar, insere na posicao correta segundo `order` (a ordem exigida
    pelo XSD do POM 4.0.0) em vez de apenas dar `append` no final, o que
    produziria um pom.xml invalido caso `tag` deva vir antes de algum
    elemento ja existente.
    """
    existing = container.find(f"{ns}{tag}")
    if existing is not None:
        return existing

    new_el = etree.Element(f"{ns}{tag}")
    target_idx = order.index(tag)

    next_sibling = next(
        (
            child
            for child in container
            if etree.QName(child).localname in order
            and order.index(etree.QName(child).localname) > target_idx
        ),
        None,
    )

    if next_sibling is None:
        append_with_matching_indent(container, new_el)
        return new_el

    previous = next_sibling.getprevious()
    separator = previous.tail if previous is not None else container.text
    next_sibling.addprevious(new_el)
    new_el.tail = separator
    return new_el
