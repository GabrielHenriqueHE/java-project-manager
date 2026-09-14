from pathlib import Path

from lxml import etree

from manager.adapters.base import BuildToolAdapter
from manager.adapters.maven.directory import detect_directory_structure
from manager.adapters.maven.parser import MavenPomParser
from manager.models import BuildFile, Dependency, Module, Project, ProjectMetadata


class MavenAdapter(BuildToolAdapter):
    build_tool = "maven"

    def __init__(self, parser: MavenPomParser | None = None):
        self._parser = parser or MavenPomParser()

    def detect(self, root_path: Path) -> bool:
        pom_path = root_path / "pom.xml"
        if not pom_path.is_file():
            return False
        try:
            root = etree.parse(str(pom_path)).getroot()
        except etree.XMLSyntaxError:
            return False
        return etree.QName(root).localname == "project"

    def infer_structure(self, root_path: Path) -> Project:
        root_path = root_path.resolve()
        pom_path = root_path / "pom.xml"
        if not pom_path.is_file():
            raise FileNotFoundError(f"pom.xml nao encontrado em {root_path}")

        managed_dependencies: list[Dependency] = []
        root_module = self._build_module(pom_path, root_path, managed_dependencies)

        return Project(
            name=root_module.metadata.name or root_module.metadata.artifact_id,
            build_tool="maven",
            root_path=root_path,
            root_module=root_module,
            managed_dependencies=managed_dependencies,
        )

    def _build_module(
        self, pom_path: Path, root_path: Path, managed_acc: list[Dependency]
    ) -> Module:
        parsed = self._parser.parse(pom_path)
        module_dir = pom_path.parent

        managed_acc.extend(parsed.managed_dependencies)

        submodules = [
            self._build_module(module_dir / name / "pom.xml", root_path, managed_acc)
            for name in parsed.module_names
        ]

        is_bom = parsed.metadata.packaging == "pom" and bool(
            parsed.managed_dependencies
        )

        return Module(
            name=parsed.metadata.artifact_id,
            relative_path=module_dir.relative_to(root_path),
            metadata=parsed.metadata,
            dependencies=parsed.dependencies + parsed.managed_dependencies,
            directory_structure=detect_directory_structure(module_dir),
            build_file=BuildFile(path=pom_path.relative_to(root_path)),
            submodules=submodules,
            is_bom=is_bom,
        )

    def add_module(
        self, project: Project, module: Module, *, parent_name: str | None = None
    ) -> Project:
        raise NotImplementedError("add_module chega na Fase 2")

    def remove_module(
        self, project: Project, module_name: str, *, force: bool = False
    ) -> Project:
        raise NotImplementedError("remove_module chega na Fase 2")

    def update_dependency(
        self, project: Project, module_name: str, dependency: Dependency
    ) -> Project:
        raise NotImplementedError("update_dependency chega na Fase 2")

    def update_metadata(
        self, project: Project, module_name: str, metadata: ProjectMetadata
    ) -> Project:
        raise NotImplementedError("update_metadata chega na Fase 2")
