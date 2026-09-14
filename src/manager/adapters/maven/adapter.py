from pathlib import Path

from lxml import etree

from manager.adapters.base import BuildToolAdapter, DependentModuleConflict
from manager.adapters.maven.directory import detect_directory_structure
from manager.adapters.maven.parser import MavenPomParser
from manager.adapters.maven.writer import MavenPomWriter
from manager.models import BuildFile, Dependency, Module, Project, ProjectMetadata


class MavenAdapter(BuildToolAdapter):
    build_tool = "maven"

    def __init__(
        self,
        parser: MavenPomParser | None = None,
        writer: MavenPomWriter | None = None,
    ):
        self._parser = parser or MavenPomParser()
        self._writer = writer or MavenPomWriter()

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
        target = self._find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        parent = self._find_parent(project.root_module, target)
        if parent is None:
            raise ValueError("Nao e possivel remover o modulo raiz do projeto")

        dependents = self._find_dependents(project.root_module, target)
        if dependents and not force:
            raise DependentModuleConflict(
                module_name, dependents=[m.name for m in dependents]
            )

        root_path = project.root_path
        group_id = target.metadata.group_id
        artifact_id = target.metadata.artifact_id

        parent_pom = root_path / parent.build_file.path
        module_value = str(target.relative_path.relative_to(parent.relative_path))
        self._writer.remove_module_entry(parent_pom, module_value)

        bom_module = self._find_bom_module(project.root_module)
        if bom_module is not None and bom_module.relative_path != target.relative_path:
            bom_pom = root_path / bom_module.build_file.path
            self._writer.remove_managed_dependency(bom_pom, group_id, artifact_id)

        for dependent in dependents:
            dependent_pom = root_path / dependent.build_file.path
            self._writer.remove_dependency(dependent_pom, group_id, artifact_id)

        return self.infer_structure(root_path)

    def _find_module(self, module: Module, name: str) -> Module | None:
        if module.name == name:
            return module
        for sub in module.submodules:
            found = self._find_module(sub, name)
            if found is not None:
                return found
        return None

    def _find_parent(self, module: Module, target: Module) -> Module | None:
        for sub in module.submodules:
            if sub.relative_path == target.relative_path:
                return module
            found = self._find_parent(sub, target)
            if found is not None:
                return found
        return None

    def _find_bom_module(self, module: Module) -> Module | None:
        if module.is_bom:
            return module
        for sub in module.submodules:
            found = self._find_bom_module(sub)
            if found is not None:
                return found
        return None

    def _find_dependents(self, root_module: Module, target: Module) -> list[Module]:
        target_key = (target.metadata.group_id, target.metadata.artifact_id)
        dependents: list[Module] = []

        def walk(module: Module) -> None:
            if module.relative_path != target.relative_path:
                for dep in module.dependencies:
                    if (
                        not dep.managed
                        and (dep.group_id, dep.artifact_id) == target_key
                    ):
                        dependents.append(module)
                        break
            for sub in module.submodules:
                walk(sub)

        walk(root_module)
        return dependents

    def update_dependency(
        self, project: Project, module_name: str, dependency: Dependency
    ) -> Project:
        raise NotImplementedError("update_dependency chega na Fase 2")

    def update_metadata(
        self, project: Project, module_name: str, metadata: ProjectMetadata
    ) -> Project:
        raise NotImplementedError("update_metadata chega na Fase 2")
