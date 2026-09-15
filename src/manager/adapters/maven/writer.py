from pathlib import Path

from lxml import etree

from manager.adapters.maven.xml_utils import (
    POM_ELEMENT_ORDER,
    append_with_matching_indent,
    ensure_child_in_order,
    namespace_of,
    remove_element_preserving_whitespace,
)
from manager.models import Dependency

JAVA_VERSION_PROPERTIES = ("maven.compiler.source", "maven.compiler.target")
DEPENDENCY_CHILD_ORDER = [
    "groupId",
    "artifactId",
    "version",
    "type",
    "classifier",
    "scope",
]

POM_NS = "http://maven.apache.org/POM/4.0.0"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


class MavenPomWriter:
    """Aplica mutacoes pontuais em um pom.xml existente, preservando formatacao.

    Cada metodo le o arquivo, aplica uma unica mutacao e grava de volta no
    mesmo arquivo. Retorna True se algo foi de fato alterado.
    """

    def add_module_entry(self, pom_path: Path, module_value: str) -> bool:
        """Adiciona <module>module_value</module> em <modules>.

        Retorna False (sem alterar nada) se o pom nao tiver uma secao
        <modules> existente, ou se a entrada ja estiver presente.
        """
        tree, root, ns = self._parse(pom_path)
        modules_el = root.find(f"{ns}modules")
        if modules_el is None:
            return False

        for module_el in modules_el.findall(f"{ns}module"):
            if module_el.text and module_el.text.strip() == module_value:
                return False

        new_el = etree.Element(f"{ns}module")
        new_el.text = module_value
        append_with_matching_indent(modules_el, new_el)

        self._write(tree, pom_path)
        return True

    def create_pom(
        self,
        pom_path: Path,
        *,
        parent_group_id: str,
        parent_artifact_id: str,
        parent_version: str,
        artifact_id: str,
        group_id: str | None = None,
        version: str | None = None,
        packaging: str = "jar",
        name: str | None = None,
        description: str | None = None,
        dependencies: list[Dependency] | None = None,
    ) -> None:
        """Cria um pom.xml novo, filho do modulo indicado por parent_*."""
        nsmap = {None: POM_NS, "xsi": XSI_NS}
        root = etree.Element(f"{{{POM_NS}}}project", nsmap=nsmap)
        root.set(
            f"{{{XSI_NS}}}schemaLocation",
            f"{POM_NS} http://maven.apache.org/xsd/maven-4.0.0.xsd",
        )

        def child(
            parent: etree._Element, tag: str, text: str | None = None
        ) -> etree._Element:
            el = etree.SubElement(parent, f"{{{POM_NS}}}{tag}")
            if text is not None:
                el.text = text
            return el

        child(root, "modelVersion", "4.0.0")

        parent_el = child(root, "parent")
        child(parent_el, "groupId", parent_group_id)
        child(parent_el, "artifactId", parent_artifact_id)
        child(parent_el, "version", parent_version)

        child(root, "artifactId", artifact_id)
        if group_id:
            child(root, "groupId", group_id)
        if version:
            child(root, "version", version)
        child(root, "packaging", packaging)
        if name:
            child(root, "name", name)
        if description:
            child(root, "description", description)

        managed = [dep for dep in dependencies or [] if dep.managed]
        direct = [dep for dep in dependencies or [] if not dep.managed]

        if managed:
            dep_mgmt_el = child(root, "dependencyManagement")
            deps_el = child(dep_mgmt_el, "dependencies")
            for dep in managed:
                self._append_dependency_element(deps_el, dep)

        if direct:
            deps_el = child(root, "dependencies")
            for dep in direct:
                self._append_dependency_element(deps_el, dep)

        tree = etree.ElementTree(root)
        etree.indent(tree, space="  ")
        pom_path.parent.mkdir(parents=True, exist_ok=True)
        self._write(tree, pom_path)

    def _append_dependency_element(
        self, deps_el: etree._Element, dependency: Dependency
    ) -> None:
        """Monta um <dependency> desanexado e o anexa a deps_el.

        Constroi o elemento desanexado (em vez de SubElement direto em
        deps_el) para poder indentar seus filhos internamente via
        `etree.indent` apos anexado, sem depender de um `etree.indent(tree)`
        global no chamador (que reformataria o pom.xml inteiro em edicoes
        pontuais como `update_dependency`; `create_pom` ja faz esse indent
        global no final, entao aqui e redundante mas inofensivo para ele).
        """
        dep_el = etree.Element(f"{{{POM_NS}}}dependency")
        etree.SubElement(dep_el, f"{{{POM_NS}}}groupId").text = dependency.group_id
        etree.SubElement(dep_el, f"{{{POM_NS}}}artifactId").text = (
            dependency.artifact_id
        )
        if dependency.version:
            etree.SubElement(dep_el, f"{{{POM_NS}}}version").text = dependency.version
        if dependency.type:
            etree.SubElement(dep_el, f"{{{POM_NS}}}type").text = dependency.type
        if dependency.classifier:
            etree.SubElement(dep_el, f"{{{POM_NS}}}classifier").text = (
                dependency.classifier
            )
        if dependency.scope:
            etree.SubElement(dep_el, f"{{{POM_NS}}}scope").text = dependency.scope

        append_with_matching_indent(deps_el, dep_el)
        depth = sum(1 for _ in dep_el.iterancestors())
        etree.indent(dep_el, space="  ", level=depth)

    def update_metadata(
        self,
        pom_path: Path,
        *,
        group_id: str | None,
        version: str | None,
        name: str | None,
        description: str | None,
        packaging: str,
        java_version: str | None,
    ) -> None:
        """Atualiza os metadados escalares de um modulo (nao mexe em artifactId).

        Cada campo opcional (`group_id`, `version`, `name`, `description`) e
        gravado quando truthy e removido quando vazio/None; `packaging` e
        sempre gravado explicitamente. `java_version` atualiza (ou remove) o
        par de properties `maven.compiler.source`/`maven.compiler.target`.
        """
        tree, root, ns = self._parse(pom_path)

        self._set_or_remove_scalar(root, "groupId", group_id, ns)
        self._set_or_remove_scalar(root, "version", version, ns)
        ensure_child_in_order(root, "packaging", ns).text = packaging
        self._set_or_remove_scalar(root, "name", name, ns)
        self._set_or_remove_scalar(root, "description", description, ns)
        self._set_java_version(root, java_version, ns)

        self._write(tree, pom_path)

    @staticmethod
    def _set_or_remove_scalar(
        root: etree._Element,
        tag: str,
        value: str | None,
        ns: str,
        order: list[str] = POM_ELEMENT_ORDER,
    ) -> None:
        if value:
            ensure_child_in_order(root, tag, ns, order).text = value
            return
        existing = root.find(f"{ns}{tag}")
        if existing is not None:
            remove_element_preserving_whitespace(existing)

    def update_dependency(self, pom_path: Path, dependency: Dependency) -> None:
        """Adiciona ou atualiza (upsert por groupId:artifactId) uma <dependency>.

        Escreve em <dependencyManagement><dependencies> se
        `dependency.managed`, senao em <dependencies> direto do modulo.
        Cria as secoes ausentes respeitando a ordem do XSD do POM.
        """
        tree, root, ns = self._parse(pom_path)

        if dependency.managed:
            dep_mgmt_el = ensure_child_in_order(root, "dependencyManagement", ns)
            deps_el = ensure_child_in_order(dep_mgmt_el, "dependencies", ns)
        else:
            deps_el = ensure_child_in_order(root, "dependencies", ns)

        existing = self._find_dependency_element(
            deps_el, ns, dependency.group_id, dependency.artifact_id
        )
        if existing is None:
            self._append_dependency_element(deps_el, dependency)
        else:
            self._set_or_remove_scalar(
                existing, "version", dependency.version, ns, DEPENDENCY_CHILD_ORDER
            )
            self._set_or_remove_scalar(
                existing, "type", dependency.type, ns, DEPENDENCY_CHILD_ORDER
            )
            self._set_or_remove_scalar(
                existing,
                "classifier",
                dependency.classifier,
                ns,
                DEPENDENCY_CHILD_ORDER,
            )
            self._set_or_remove_scalar(
                existing, "scope", dependency.scope, ns, DEPENDENCY_CHILD_ORDER
            )

        self._write(tree, pom_path)

    @staticmethod
    def _find_dependency_element(
        deps_el: etree._Element, ns: str, group_id: str, artifact_id: str
    ) -> etree._Element | None:
        for dep_el in deps_el.findall(f"{ns}dependency"):
            group_el = dep_el.find(f"{ns}groupId")
            artifact_el = dep_el.find(f"{ns}artifactId")
            if (
                group_el is not None
                and group_el.text
                and group_el.text.strip() == group_id
                and artifact_el is not None
                and artifact_el.text
                and artifact_el.text.strip() == artifact_id
            ):
                return dep_el
        return None

    @staticmethod
    def _set_java_version(
        root: etree._Element, java_version: str | None, ns: str
    ) -> None:
        properties_el = root.find(f"{ns}properties")

        if java_version:
            properties_el = ensure_child_in_order(root, "properties", ns)
            for prop_tag in JAVA_VERSION_PROPERTIES:
                prop_el = properties_el.find(f"{ns}{prop_tag}")
                if prop_el is None:
                    prop_el = etree.Element(f"{ns}{prop_tag}")
                    append_with_matching_indent(properties_el, prop_el)
                prop_el.text = java_version
            return

        if properties_el is None:
            return
        for prop_tag in JAVA_VERSION_PROPERTIES:
            prop_el = properties_el.find(f"{ns}{prop_tag}")
            if prop_el is not None:
                remove_element_preserving_whitespace(prop_el)
        if len(properties_el) == 0:
            remove_element_preserving_whitespace(properties_el)

    def remove_module_entry(self, pom_path: Path, module_value: str) -> bool:
        tree, root, ns = self._parse(pom_path)
        modules_el = root.find(f"{ns}modules")
        if modules_el is None:
            return False

        removed = False
        for module_el in modules_el.findall(f"{ns}module"):
            if module_el.text and module_el.text.strip() == module_value:
                remove_element_preserving_whitespace(module_el)
                removed = True
                break

        if not removed:
            return False

        if modules_el.find(f"{ns}module") is None:
            remove_element_preserving_whitespace(modules_el)

        self._write(tree, pom_path)
        return True

    def remove_managed_dependency(
        self, pom_path: Path, group_id: str, artifact_id: str
    ) -> bool:
        tree, root, ns = self._parse(pom_path)
        dep_mgmt = root.find(f"{ns}dependencyManagement")
        deps_el = dep_mgmt.find(f"{ns}dependencies") if dep_mgmt is not None else None
        if not self._remove_matching_dependency(deps_el, ns, group_id, artifact_id):
            return False

        if deps_el.find(f"{ns}dependency") is None:
            remove_element_preserving_whitespace(deps_el)
            if dep_mgmt.find(f"{ns}dependencies") is None:
                remove_element_preserving_whitespace(dep_mgmt)

        self._write(tree, pom_path)
        return True

    def remove_dependency(
        self, pom_path: Path, group_id: str, artifact_id: str
    ) -> bool:
        tree, root, ns = self._parse(pom_path)
        deps_el = root.find(f"{ns}dependencies")
        if not self._remove_matching_dependency(deps_el, ns, group_id, artifact_id):
            return False

        if deps_el.find(f"{ns}dependency") is None:
            remove_element_preserving_whitespace(deps_el)

        self._write(tree, pom_path)
        return True

    def _remove_matching_dependency(
        self,
        deps_el: etree._Element | None,
        ns: str,
        group_id: str,
        artifact_id: str,
    ) -> bool:
        if deps_el is None:
            return False
        for dep_el in deps_el.findall(f"{ns}dependency"):
            if (
                self._child_text(dep_el, "groupId", ns) == group_id
                and self._child_text(dep_el, "artifactId", ns) == artifact_id
            ):
                remove_element_preserving_whitespace(dep_el)
                return True
        return False

    @staticmethod
    def _child_text(parent: etree._Element, tag: str, ns: str) -> str | None:
        el = parent.find(f"{ns}{tag}")
        return el.text.strip() if el is not None and el.text else None

    @staticmethod
    def _parse(pom_path: Path) -> tuple[etree._ElementTree, etree._Element, str]:
        tree = etree.parse(str(pom_path))
        root = tree.getroot()
        return tree, root, namespace_of(root)

    @staticmethod
    def _write(tree: etree._ElementTree, pom_path: Path) -> None:
        tree.write(str(pom_path), xml_declaration=True, encoding="UTF-8")
        # lxml sempre serializa a declaracao XML com aspas simples; normaliza
        # para aspas duplas (padrao do Maven) para minimizar o diff cosmetico.
        content = pom_path.read_bytes()
        content = content.replace(
            b"<?xml version='1.0' encoding='UTF-8'?>",
            b'<?xml version="1.0" encoding="UTF-8"?>',
        )
        pom_path.write_bytes(content)
