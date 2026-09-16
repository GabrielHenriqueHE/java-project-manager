from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from manager.adapters.maven import build_helper
from manager.adapters.maven.xml_utils import namespace_of
from manager.models import Dependency, DirectoryRole, ProjectMetadata


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
    registered_directories: list[tuple[str, DirectoryRole]] = field(
        default_factory=list
    )


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
        ns = namespace_of(root)

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

        registered_directories = self._parse_registered_directories(
            root.find(f"{ns}build"), ns
        )

        return ParsedPom(
            pom_path=pom_path,
            metadata=metadata,
            parent=parent,
            dependencies=dependencies,
            managed_dependencies=managed_dependencies,
            module_names=module_names,
            registered_directories=registered_directories,
        )

    def _parse_registered_directories(
        self, build_el: etree._Element | None, ns: str
    ) -> list[tuple[str, DirectoryRole]]:
        """Le de volta os diretorios ja registrados como fonte/recurso extra
        via org.codehaus.mojo:build-helper-maven-plugin (escrito por
        MavenPomWriter.register_directory_role). Ignora silenciosamente
        qualquer <build><plugins> que nao siga esse formato - nao e papel
        da inferencia validar configuracao de build de terceiros.
        """
        if build_el is None:
            return []
        plugins_el = build_el.find(f"{ns}plugins")
        if plugins_el is None:
            return []

        registered: list[tuple[str, DirectoryRole]] = []
        for plugin_el in plugins_el.findall(f"{ns}plugin"):
            if not self._is_build_helper_plugin(plugin_el, ns):
                continue
            executions_el = plugin_el.find(f"{ns}executions")
            if executions_el is None:
                continue
            for execution_el in executions_el.findall(f"{ns}execution"):
                registered.extend(self._parse_execution_directories(execution_el, ns))
        return registered

    @classmethod
    def _is_build_helper_plugin(cls, plugin_el: etree._Element, ns: str) -> bool:
        return (
            cls._text(plugin_el, "groupId", ns) == build_helper.GROUP_ID
            and cls._text(plugin_el, "artifactId", ns) == build_helper.ARTIFACT_ID
        )

    @classmethod
    def _parse_execution_directories(
        cls, execution_el: etree._Element, ns: str
    ) -> list[tuple[str, DirectoryRole]]:
        goals_el = execution_el.find(f"{ns}goals")
        if goals_el is None:
            return []
        goal = cls._text(goals_el, "goal", ns)
        role = build_helper.GOAL_ROLE.get(goal) if goal else None
        if role is None:
            return []

        config_el = execution_el.find(f"{ns}configuration")
        if config_el is None:
            return []

        if role in ("source", "test-source"):
            sources_el = config_el.find(f"{ns}sources")
            if sources_el is None:
                return []
            return [
                (el.text.strip(), role)
                for el in sources_el.findall(f"{ns}source")
                if el.text
            ]

        resources_el = config_el.find(f"{ns}resources")
        if resources_el is None:
            return []
        paths = [
            cls._text(resource_el, "directory", ns)
            for resource_el in resources_el.findall(f"{ns}resource")
        ]
        return [(path, role) for path in paths if path]

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
