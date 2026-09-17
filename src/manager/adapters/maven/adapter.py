import shutil
from pathlib import Path

from lxml import etree

from manager.adapters.base import (
    BuildToolAdapter,
    DependentModuleConflict,
    DirectoryNotEmptyConflict,
)
from manager.adapters.common.lookup import (
    find_bom_module,
    find_dependents,
    find_managed_dependency_owner,
    find_module,
    find_parent,
    resolve_module_relative_path,
)
from manager.adapters.maven.directory import (
    STANDARD_DIRS,
    detect_directory_structure,
    merge_registered_directories,
)
from manager.adapters.maven.parser import MavenPomParser
from manager.adapters.maven.writer import MavenPomWriter
from manager.manifest import ModuleManifest, is_bom_manifest, validate_manifest_tree
from manager.models import (
    BuildFile,
    Dependency,
    DirectoryRole,
    DirectoryStructure,
    Module,
    Project,
    ProjectMetadata,
)

_REGISTERABLE_ROLES: frozenset[DirectoryRole] = frozenset(
    {"source", "test-source", "resource", "test-resource"}
)


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

        directory_structure = detect_directory_structure(module_dir)
        merge_registered_directories(
            directory_structure, module_dir, parsed.registered_directories
        )

        return Module(
            name=parsed.metadata.artifact_id,
            relative_path=module_dir.relative_to(root_path),
            metadata=parsed.metadata,
            dependencies=parsed.dependencies + parsed.managed_dependencies,
            directory_structure=directory_structure,
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
        self,
        project: Project,
        module_name: str,
        relative_path: Path,
        *,
        force: bool = False,
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
            if not force:
                raise DirectoryNotEmptyConflict(str(relative_path))
            shutil.rmtree(target_path)
        else:
            target_path.rmdir()

        return self.infer_structure(project.root_path)

    def _resolve_module_relative_path(
        self, project: Project, target: Module, relative_path: Path
    ) -> Path:
        return resolve_module_relative_path(project, target, relative_path)

    def _find_module(self, module: Module, name: str) -> Module | None:
        return find_module(module, name)

    def _find_parent(self, module: Module, target: Module) -> Module | None:
        return find_parent(module, target)

    def _find_bom_module(self, module: Module) -> Module | None:
        return find_bom_module(module)

    def _find_dependents(self, root_module: Module, target: Module) -> list[Module]:
        return find_dependents(root_module, target)

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

    def remove_direct_dependency(
        self, project: Project, module_name: str, group_id: str, artifact_id: str
    ) -> Project:
        target = self._find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        pom_path = project.root_path / target.build_file.path
        if not self._writer.remove_dependency(pom_path, group_id, artifact_id):
            raise ValueError(
                f"Dependencia direta '{group_id}:{artifact_id}' nao encontrada em "
                f"'{target.name}'"
            )

        return self.infer_structure(project.root_path)

    def _find_managed_dependency_owner(
        self, module: Module, group_id: str, artifact_id: str
    ) -> Module | None:
        return find_managed_dependency_owner(module, group_id, artifact_id)

    def register_directory_role(
        self,
        project: Project,
        module_name: str,
        relative_path: Path,
        role: DirectoryRole,
    ) -> Project:
        target = self._find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        if role not in _REGISTERABLE_ROLES:
            raise ValueError(
                f"role invalido: '{role}' (use um de {sorted(_REGISTERABLE_ROLES)})"
            )

        target_path = self._resolve_module_relative_path(project, target, relative_path)
        if not target_path.is_dir():
            raise ValueError(f"'{relative_path}' nao existe; crie o diretorio primeiro")

        pom_path = project.root_path / target.build_file.path
        self._writer.register_directory_role(pom_path, str(relative_path), role)

        return self.infer_structure(project.root_path)

    def unregister_directory_role(
        self,
        project: Project,
        module_name: str,
        relative_path: Path,
        role: DirectoryRole,
    ) -> Project:
        target = self._find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        if role not in _REGISTERABLE_ROLES:
            raise ValueError(
                f"role invalido: '{role}' (use um de {sorted(_REGISTERABLE_ROLES)})"
            )

        pom_path = project.root_path / target.build_file.path
        if not self._writer.unregister_directory_role(
            pom_path, str(relative_path), role
        ):
            raise ValueError(
                f"'{relative_path}' nao esta registrado como {role} no build "
                f"de '{target.name}'"
            )

        return self.infer_structure(project.root_path)

    def create_project(
        self,
        manifest: ModuleManifest,
        destination_path: Path,
        *,
        source_root: Path | None = None,
    ) -> Project:
        validate_manifest_tree(manifest)
        self._validate_maven_manifest(manifest, is_root=True)

        destination_path = destination_path.resolve()
        if destination_path.exists() and any(destination_path.iterdir()):
            raise ValueError(f"'{destination_path}' ja existe e nao esta vazio")
        destination_path.mkdir(parents=True, exist_ok=True)

        self._materialize(manifest, destination_path, None, None, None, source_root)

        return self.infer_structure(destination_path)

    def _validate_maven_manifest(
        self, module: ModuleManifest, *, is_root: bool
    ) -> None:
        if is_root and (not module.metadata.group_id or not module.metadata.version):
            raise ValueError(
                "Modulo raiz nao tem parent para herdar: "
                "groupId e version sao obrigatorios"
            )

        is_bom = is_bom_manifest(module)
        if (module.submodules or is_bom) and module.metadata.packaging != "pom":
            raise ValueError(
                f"Modulo '{module.metadata.artifact_id}' tem submodulos ou e BOM; "
                "packaging precisa ser 'pom'"
            )

        for dep in module.dependencies:
            if dep.managed and not dep.version:
                raise ValueError(
                    f"Dependencia gerenciada '{dep.group_id}:{dep.artifact_id}' "
                    "precisa de version"
                )

        for sub in module.submodules:
            self._validate_maven_manifest(sub, is_root=False)

    def _materialize(
        self,
        module: ModuleManifest,
        module_dir: Path,
        parent_artifact_id: str | None,
        effective_group_id: str | None,
        effective_version: str | None,
        source_root: Path | None,
    ) -> tuple[str | None, str | None]:
        artifact_id = module.metadata.artifact_id
        submodule_names = [
            sub.metadata.artifact_id for sub in module.submodules
        ] or None

        if parent_artifact_id is None:
            own_group_id = module.metadata.group_id
            own_version = module.metadata.version
            self._writer.create_pom(
                module_dir / "pom.xml",
                artifact_id=artifact_id,
                group_id=own_group_id,
                version=own_version,
                packaging=module.metadata.packaging,
                name=module.metadata.name,
                description=module.metadata.description,
                dependencies=module.dependencies,
                submodule_names=submodule_names,
            )
        else:
            own_group_id = module.metadata.group_id or effective_group_id
            own_version = module.metadata.version or effective_version
            write_group_id = (
                module.metadata.group_id
                if module.metadata.group_id
                and module.metadata.group_id != effective_group_id
                else None
            )
            write_version = (
                module.metadata.version
                if module.metadata.version
                and module.metadata.version != effective_version
                else None
            )
            self._writer.create_pom(
                module_dir / "pom.xml",
                parent_group_id=effective_group_id,
                parent_artifact_id=parent_artifact_id,
                parent_version=effective_version,
                artifact_id=artifact_id,
                group_id=write_group_id,
                version=write_version,
                packaging=module.metadata.packaging,
                name=module.metadata.name,
                description=module.metadata.description,
                dependencies=module.dependencies,
                submodule_names=submodule_names,
            )

        self._materialize_directories(
            module_dir, module.directory_structure, source_root, artifact_id
        )

        for sub in module.submodules:
            self._materialize(
                sub,
                module_dir / sub.metadata.artifact_id,
                artifact_id,
                own_group_id,
                own_version,
                source_root,
            )

        return own_group_id, own_version

    def _materialize_directories(
        self,
        module_dir: Path,
        structure: DirectoryStructure,
        source_root: Path | None,
        artifact_id: str,
    ) -> None:
        module_snapshot = (source_root / artifact_id) if source_root else None
        role_dirs: dict[DirectoryRole, list[str]] = {
            "source": structure.source_dirs,
            "test-source": structure.test_dirs,
            "resource": structure.resource_dirs,
            "test-resource": structure.test_resource_dirs,
        }
        for role, dirs in role_dirs.items():
            for rel_dir in dirs:
                target = module_dir / rel_dir
                snapshot = (module_snapshot / rel_dir) if module_snapshot else None
                if snapshot is not None and snapshot.is_dir():
                    shutil.copytree(snapshot, target, dirs_exist_ok=True)
                else:
                    target.mkdir(parents=True, exist_ok=True)
                if rel_dir != STANDARD_DIRS[role]:
                    self._writer.register_directory_role(
                        module_dir / "pom.xml", rel_dir, role
                    )
