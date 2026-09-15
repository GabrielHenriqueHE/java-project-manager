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
        root_path = project.root_path

        if parent_name is None:
            parent = project.root_module
        else:
            parent = self._find_module(project.root_module, parent_name)
            if parent is None:
                raise ValueError(
                    f"Modulo pai '{parent_name}' nao encontrado no projeto"
                )

        if parent.metadata.packaging != "pom":
            raise ValueError(
                f"Modulo pai '{parent.name}' precisa ter packaging 'pom' para "
                "receber novos modulos"
            )

        artifact_id = module.metadata.artifact_id
        if self._find_module(project.root_module, artifact_id) is not None:
            raise ValueError(f"Ja existe um modulo chamado '{artifact_id}' no projeto")

        parent_dir = root_path / parent.relative_path
        module_dir = parent_dir / artifact_id
        if module_dir.exists():
            raise ValueError(f"O diretorio '{module_dir}' ja existe")

        group_id = (
            module.metadata.group_id
            if module.metadata.group_id
            and module.metadata.group_id != parent.metadata.group_id
            else None
        )
        version = (
            module.metadata.version
            if module.metadata.version
            and module.metadata.version != parent.metadata.version
            else None
        )

        self._writer.create_pom(
            module_dir / "pom.xml",
            parent_group_id=parent.metadata.group_id or "",
            parent_artifact_id=parent.metadata.artifact_id,
            parent_version=parent.metadata.version or "",
            artifact_id=artifact_id,
            group_id=group_id,
            version=version,
            packaging=module.metadata.packaging,
            name=module.metadata.name,
            description=module.metadata.description,
            dependencies=module.dependencies,
        )

        directory_structure = module.directory_structure
        all_dirs = {
            *directory_structure.source_dirs,
            *directory_structure.test_dirs,
            *directory_structure.resource_dirs,
            *directory_structure.test_resource_dirs,
        }
        for rel_dir in all_dirs:
            (module_dir / rel_dir).mkdir(parents=True, exist_ok=True)

        parent_pom = root_path / parent.build_file.path
        if not self._writer.add_module_entry(parent_pom, artifact_id):
            raise ValueError(
                f"O pom de '{parent.name}' nao possui uma secao <modules> existente"
            )

        return self.infer_structure(root_path)

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

    def add_directory(
        self, project: Project, module_name: str, relative_path: Path
    ) -> Project:
        target = self._find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        target_path = self._resolve_module_relative_path(project, target, relative_path)

        if target_path.exists():
            raise ValueError(f"'{relative_path}' ja existe")

        target_path.mkdir(parents=True)

        return self.infer_structure(project.root_path)

    def remove_directory(
        self, project: Project, module_name: str, relative_path: Path
    ) -> Project:
        target = self._find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        target_path = self._resolve_module_relative_path(project, target, relative_path)

        module_dir = (project.root_path / target.relative_path).resolve()
        if target_path == module_dir:
            raise ValueError("Nao e possivel remover o diretorio raiz do modulo")

        if not target_path.exists():
            raise ValueError(f"'{relative_path}' nao existe")

        if any(target_path.iterdir()):
            raise ValueError(f"'{relative_path}' nao esta vazio")

        target_path.rmdir()

        return self.infer_structure(project.root_path)

    def _resolve_module_relative_path(
        self, project: Project, target: Module, relative_path: Path
    ) -> Path:
        module_dir = (project.root_path / target.relative_path).resolve()
        target_path = (module_dir / relative_path).resolve()
        if module_dir not in (target_path, *target_path.parents):
            raise ValueError(
                f"'{relative_path}' escapa do diretorio do modulo '{target.name}'"
            )
        return target_path

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
        target = self._find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        if not dependency.group_id or not dependency.artifact_id:
            raise ValueError("groupId e artifactId sao obrigatorios")

        if dependency.managed:
            if target.metadata.packaging != "pom":
                raise ValueError(
                    f"Modulo '{target.name}' precisa ter packaging 'pom' para "
                    "receber uma dependencia gerenciada"
                )
            if not dependency.version:
                raise ValueError(
                    "version e obrigatoria para uma dependencia gerenciada"
                )

        pom_path = project.root_path / target.build_file.path
        self._writer.update_dependency(pom_path, dependency)

        return self.infer_structure(project.root_path)

    def update_metadata(
        self, project: Project, module_name: str, metadata: ProjectMetadata
    ) -> Project:
        target = self._find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        if metadata.artifact_id != target.metadata.artifact_id:
            raise ValueError("Renomear artifactId nao e suportado")

        if (
            metadata.packaging != "pom"
            and metadata.packaging != target.metadata.packaging
            and (target.submodules or target.is_bom)
        ):
            raise ValueError(
                f"Modulo '{target.name}' tem submodulos ou e o BOM do projeto; "
                "packaging precisa continuar 'pom'"
            )

        parent = self._find_parent(project.root_module, target)
        if parent is None:
            if not metadata.group_id or not metadata.version:
                raise ValueError(
                    "Modulo raiz nao tem <parent> para herdar: "
                    "groupId e version sao obrigatorios"
                )
            group_id = metadata.group_id
            version = metadata.version
        else:
            group_id = (
                metadata.group_id
                if metadata.group_id and metadata.group_id != parent.metadata.group_id
                else None
            )
            version = (
                metadata.version
                if metadata.version and metadata.version != parent.metadata.version
                else None
            )

        java_version = metadata.properties.get("maven.compiler.source") or None

        pom_path = project.root_path / target.build_file.path
        self._writer.update_metadata(
            pom_path,
            group_id=group_id,
            version=version,
            name=metadata.name,
            description=metadata.description,
            packaging=metadata.packaging,
            java_version=java_version,
        )

        return self.infer_structure(project.root_path)

    def remove_dependency(
        self, project: Project, group_id: str, artifact_id: str
    ) -> Project:
        owner = self._find_managed_dependency_owner(
            project.root_module, group_id, artifact_id
        )
        if owner is None:
            raise ValueError(
                f"Dependencia gerenciada '{group_id}:{artifact_id}' nao encontrada"
            )

        pom_path = project.root_path / owner.build_file.path
        self._writer.remove_managed_dependency(pom_path, group_id, artifact_id)

        return self.infer_structure(project.root_path)

    def _find_managed_dependency_owner(
        self, module: Module, group_id: str, artifact_id: str
    ) -> Module | None:
        for dep in module.dependencies:
            if (
                dep.managed
                and dep.group_id == group_id
                and dep.artifact_id == artifact_id
            ):
                return module
        for sub in module.submodules:
            found = self._find_managed_dependency_owner(sub, group_id, artifact_id)
            if found is not None:
                return found
        return None
