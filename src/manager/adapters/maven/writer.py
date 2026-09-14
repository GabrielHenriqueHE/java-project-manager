from pathlib import Path

from lxml import etree

from manager.adapters.maven.xml_utils import (
    append_with_matching_indent,
    namespace_of,
    remove_element_preserving_whitespace,
)
from manager.models import Dependency

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
        dep_el = etree.SubElement(deps_el, f"{{{POM_NS}}}dependency")
        etree.SubElement(dep_el, f"{{{POM_NS}}}groupId").text = dependency.group_id
        etree.SubElement(dep_el, f"{{{POM_NS}}}artifactId").text = (
            dependency.artifact_id
        )
        if dependency.version:
            etree.SubElement(dep_el, f"{{{POM_NS}}}version").text = dependency.version
        if dependency.scope:
            etree.SubElement(dep_el, f"{{{POM_NS}}}scope").text = dependency.scope

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
