from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from manager.models import Dependency, ProjectMetadata


@dataclass
class ParentRef:
    group_id: str
    artifact_id: str
    version: str


@dataclass
class ParsedPom:
    pom_path: Path
    metadata: ProjectMetadata
    parent: ParentRef | None
    dependencies: list[Dependency] = field(default_factory=list)
    managed_dependencies: list[Dependency] = field(default_factory=list)
    module_names: list[str] = field(default_factory=list)


class MavenPomParser:
    """Le um pom.xml isolado e extrai metadata, dependencias e modulos filhos.

    Nao resolve heranca entre modulos (isso e responsabilidade de quem
    monta a arvore completa, ja que exige visao de todos os poms).
    """

    def parse(self, pom_path: Path) -> ParsedPom:
        try:
            tree = etree.parse(str(pom_path))
        except etree.XMLSyntaxError as exc:
            raise ValueError(f"pom.xml invalido em {pom_path}: {exc}") from exc

        root = tree.getroot()
        ns = self._namespace(root)

        parent_el = root.find(f"{ns}parent")
        parent = None
        if parent_el is not None:
            parent = ParentRef(
                group_id=self._text(parent_el, "groupId", ns) or "",
                artifact_id=self._text(parent_el, "artifactId", ns) or "",
                version=self._text(parent_el, "version", ns) or "",
            )

        artifact_id = self._text(root, "artifactId", ns)
        if not artifact_id:
            raise ValueError(f"pom.xml sem artifactId: {pom_path}")

        group_id = self._text(root, "groupId", ns) or (
            parent.group_id if parent else None
        )
        version = self._text(root, "version", ns) or (
            parent.version if parent else None
        )

        metadata = ProjectMetadata(
            group_id=group_id,
            artifact_id=artifact_id,
            version=version,
            name=self._text(root, "name", ns),
            description=self._text(root, "description", ns),
            packaging=self._text(root, "packaging", ns) or "jar",
            properties=self._parse_properties(root.find(f"{ns}properties"), ns),
        )

        dependencies = self._parse_dependencies(
            root.find(f"{ns}dependencies"), ns, managed=False
        )

        managed_dependencies: list[Dependency] = []
        dep_mgmt = root.find(f"{ns}dependencyManagement")
        if dep_mgmt is not None:
            managed_dependencies = self._parse_dependencies(
                dep_mgmt.find(f"{ns}dependencies"), ns, managed=True
            )

        module_names: list[str] = []
        modules_el = root.find(f"{ns}modules")
        if modules_el is not None:
            module_names = [
                el.text.strip() for el in modules_el.findall(f"{ns}module") if el.text
            ]

        return ParsedPom(
            pom_path=pom_path,
            metadata=metadata,
            parent=parent,
            dependencies=dependencies,
            managed_dependencies=managed_dependencies,
            module_names=module_names,
        )

    @staticmethod
    def _namespace(root: etree._Element) -> str:
        if root.tag.startswith("{"):
            uri = root.tag[1 : root.tag.index("}")]
            return f"{{{uri}}}"
        return ""

    @staticmethod
    def _text(parent: etree._Element, tag: str, ns: str) -> str | None:
        el = parent.find(f"{ns}{tag}")
        return el.text.strip() if el is not None and el.text else None

    @staticmethod
    def _parse_properties(
        properties_el: etree._Element | None, ns: str
    ) -> dict[str, str]:
        if properties_el is None:
            return {}
        properties: dict[str, str] = {}
        for child in properties_el:
            if child.text:
                properties[etree.QName(child).localname] = child.text.strip()
        return properties

    def _parse_dependencies(
        self, deps_el: etree._Element | None, ns: str, *, managed: bool
    ) -> list[Dependency]:
        if deps_el is None:
            return []
        dependencies: list[Dependency] = []
        for dep_el in deps_el.findall(f"{ns}dependency"):
            group_id = self._text(dep_el, "groupId", ns)
            artifact_id = self._text(dep_el, "artifactId", ns)
            if not group_id or not artifact_id:
                continue
            dependencies.append(
                Dependency(
                    group_id=group_id,
                    artifact_id=artifact_id,
                    version=self._text(dep_el, "version", ns),
                    scope=self._text(dep_el, "scope", ns),
                    type=self._text(dep_el, "type", ns),
                    classifier=self._text(dep_el, "classifier", ns),
                    managed=managed,
                )
            )
        return dependencies
