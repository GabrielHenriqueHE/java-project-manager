import shutil
from pathlib import Path

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
from manager.adapters.gradle.directory import detect_directory_structure
from manager.adapters.gradle.parser import (
    SETTINGS_FILE_NAMES,
    ParsedGradleBuild,
    ParsedSettings,
    find_build_file,
    find_settings_file,
    parse_build_file,
    parse_settings_file,
)
from manager.adapters.gradle.writer import GradleWriter
from manager.manifest import ModuleManifest
from manager.models import (
    BuildFile,
    Dependency,
    DirectoryRole,
    Module,
    Project,
    ProjectMetadata,
)

_STUB_MESSAGE = "{method} ainda nao implementado para Gradle - fase futura"


class GradleAdapter(BuildToolAdapter):
    """Suporte a projetos Gradle (Groovy e Kotlin DSL).

    Fase 15 (fundacao): `detect`/`infer_structure`. Fase 16: primeira
    mutacao real, `add_directory`/`remove_directory` - nao exigem editar
    build.gradle(.kts) (diretorios-padrao nao precisam ser declarados no
    Gradle, ao contrario do Maven), entao sao puramente filesystem +
    `infer_structure`, mesmo comportamento do MavenAdapter. As demais
    mutacoes (criar projeto, adicionar/remover modulo, dependencias,
    registro de diretorio customizado) seguem como stubs
    `NotImplementedError` - fatias futuras.
    """

    build_tool = "gradle"

    def __init__(self, writer: GradleWriter | None = None):
        self._writer = writer or GradleWriter()

    def detect(self, root_path: Path) -> bool:
        return (
            find_build_file(root_path) is not None
            or find_settings_file(root_path) is not None
        )

    def infer_structure(self, root_path: Path) -> Project:
        root_path = root_path.resolve()

        settings_path = find_settings_file(root_path)
        settings = parse_settings_file(settings_path) if settings_path else None

        root_build_path = find_build_file(root_path)
        root_parsed = parse_build_file(root_build_path) if root_build_path else None

        managed_dependencies: list[Dependency] = []
        root_module = self._build_root_module(
            root_path, root_build_path, root_parsed, settings, managed_dependencies
        )

        return Project(
            name=root_module.metadata.name or root_module.metadata.artifact_id,
            build_tool="gradle",
            root_path=root_path,
            root_module=root_module,
            managed_dependencies=managed_dependencies,
        )

    def _build_root_module(
        self,
        root_path: Path,
        root_build_path: Path | None,
        root_parsed: ParsedGradleBuild | None,
        settings: ParsedSettings | None,
        managed_acc: list[Dependency],
    ) -> Module:
        artifact_id = (settings.root_name if settings else None) or root_path.name

        if root_parsed is not None:
            managed_acc.extend(root_parsed.managed_dependencies)
            metadata = ProjectMetadata(
                group_id=root_parsed.group_id,
                artifact_id=artifact_id,
                version=root_parsed.version,
                packaging=_packaging_from_plugins(root_parsed),
            )
            dependencies = root_parsed.dependencies + root_parsed.managed_dependencies
            is_bom = metadata.packaging == "pom" and bool(
                root_parsed.managed_dependencies
            )
            build_file_path = root_build_path
        else:
            metadata = ProjectMetadata(artifact_id=artifact_id, packaging="pom")
            dependencies = []
            is_bom = False
            build_file_path = find_settings_file(root_path)

        submodules = [
            self._build_included_module(root_path, name, relative_path, managed_acc)
            for name, relative_path in (settings.modules if settings else [])
        ]

        return Module(
            name=artifact_id,
            relative_path=Path("."),
            metadata=metadata,
            dependencies=dependencies,
            directory_structure=detect_directory_structure(root_path),
            build_file=BuildFile(path=build_file_path.relative_to(root_path)),
            submodules=submodules,
            is_bom=is_bom,
        )

    def _build_included_module(
        self,
        root_path: Path,
        name: str,
        relative_path: str,
        managed_acc: list[Dependency],
    ) -> Module:
        module_dir = root_path / relative_path
        build_path = find_build_file(module_dir)
        if build_path is None:
            raise ValueError(
                f"Modulo incluido '{name}' nao tem build.gradle nem "
                f"build.gradle.kts em '{relative_path}'"
            )

        parsed = parse_build_file(build_path)
        managed_acc.extend(parsed.managed_dependencies)

        packaging = _packaging_from_plugins(parsed)
        metadata = ProjectMetadata(
            group_id=parsed.group_id,
            artifact_id=name,
            version=parsed.version,
            packaging=packaging,
        )

        return Module(
            name=name,
            relative_path=Path(relative_path),
            metadata=metadata,
            dependencies=parsed.dependencies + parsed.managed_dependencies,
            directory_structure=detect_directory_structure(module_dir),
            build_file=BuildFile(path=build_path.relative_to(root_path)),
            submodules=[],
            is_bom=packaging == "pom" and bool(parsed.managed_dependencies),
        )

    # ---- mutacoes: stubs (fase futura) ----

    def create_project(
        self,
        manifest: ModuleManifest,
        destination_path: Path,
        *,
        source_root: Path | None = None,
    ) -> Project:
        raise NotImplementedError(_STUB_MESSAGE.format(method="create_project"))

    def add_module(
        self, project: Project, module: Module, *, parent_name: str | None = None
    ) -> Project:
        settings_path = find_settings_file(project.root_path)
        if settings_path is None:
            raise ValueError(
                f"Projeto nao tem settings.gradle(.kts) em '{project.root_path}'"
            )

        if parent_name is not None:
            parent = find_module(project.root_module, parent_name)
            if parent is None:
                raise ValueError(
                    f"Modulo pai '{parent_name}' nao encontrado no projeto"
                )
            if parent.relative_path != project.root_module.relative_path:
                raise ValueError(
                    "Gradle so suporta modulos filhos diretos da raiz nesta "
                    f"fase; '{parent_name}' nao e a raiz"
                )

        artifact_id = module.metadata.artifact_id
        if find_module(project.root_module, artifact_id) is not None:
            raise ValueError(f"Ja existe um modulo chamado '{artifact_id}' no projeto")

        module_dir = project.root_path / artifact_id
        if module_dir.exists():
            raise ValueError(f"O diretorio '{module_dir}' ja existe")

        directory_structure = module.directory_structure
        all_dirs = {
            *directory_structure.source_dirs,
            *directory_structure.test_dirs,
            *directory_structure.resource_dirs,
            *directory_structure.test_resource_dirs,
        }
        for rel_dir in all_dirs:
            (module_dir / rel_dir).mkdir(parents=True, exist_ok=True)

        build_file_name = (
            "build.gradle.kts"
            if settings_path.name.endswith(".kts")
            else "build.gradle"
        )
        self._writer.create_build_file(
            module_dir / build_file_name,
            packaging=module.metadata.packaging,
            group_id=module.metadata.group_id,
            version=module.metadata.version,
            dependencies=module.dependencies,
        )
        self._writer.add_include(settings_path, artifact_id)

        return self.infer_structure(project.root_path)

    def remove_module(
        self, project: Project, module_name: str, *, force: bool = False
    ) -> Project:
        target = find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        parent = find_parent(project.root_module, target)
        if parent is None:
            raise ValueError("Nao e possivel remover o modulo raiz do projeto")

        dependents = find_dependents(project.root_module, target)
        if dependents and not force:
            raise DependentModuleConflict(
                module_name, dependents=[m.name for m in dependents]
            )

        root_path = project.root_path
        group_id = target.metadata.group_id
        artifact_id = target.metadata.artifact_id

        settings_path = find_settings_file(root_path)
        if settings_path is not None:
            self._writer.remove_include(settings_path, artifact_id)

        bom_module = find_bom_module(project.root_module)
        if bom_module is not None and bom_module.relative_path != target.relative_path:
            bom_path = root_path / bom_module.build_file.path
            self._writer.remove_managed_dependency(bom_path, group_id, artifact_id)

        for dependent in dependents:
            dependent_path = root_path / dependent.build_file.path
            self._writer.remove_dependency(dependent_path, group_id, artifact_id)

        return self.infer_structure(root_path)

    def update_dependency(
        self, project: Project, module_name: str, dependency: Dependency
    ) -> Project:
        target = find_module(project.root_module, module_name)
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

        if target.build_file.path.name in SETTINGS_FILE_NAMES:
            raise ValueError(
                f"Modulo '{target.name}' nao tem build.gradle(.kts); crie um "
                "antes de definir dependencias"
            )

        build_path = project.root_path / target.build_file.path
        self._writer.upsert_dependency(build_path, dependency)

        return self.infer_structure(project.root_path)

    def update_metadata(
        self, project: Project, module_name: str, metadata: ProjectMetadata
    ) -> Project:
        target = find_module(project.root_module, module_name)
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

        if target.build_file.path.name in SETTINGS_FILE_NAMES:
            raise ValueError(
                f"Modulo '{target.name}' nao tem build.gradle(.kts); crie um "
                "antes de definir metadados"
            )

        packaging = (
            metadata.packaging
            if metadata.packaging != target.metadata.packaging
            else None
        )

        build_path = project.root_path / target.build_file.path
        self._writer.update_metadata(
            build_path,
            group_id=metadata.group_id,
            version=metadata.version,
            packaging=packaging,
        )

        return self.infer_structure(project.root_path)

    def add_directory(
        self, project: Project, module_name: str, relative_path: Path
    ) -> Project:
        target = find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        target_path = resolve_module_relative_path(project, target, relative_path)

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
        target = find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        target_path = resolve_module_relative_path(project, target, relative_path)

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

    def remove_dependency(
        self, project: Project, group_id: str, artifact_id: str
    ) -> Project:
        owner = find_managed_dependency_owner(
            project.root_module, group_id, artifact_id
        )
        if owner is None:
            raise ValueError(
                f"Dependencia gerenciada '{group_id}:{artifact_id}' nao encontrada"
            )

        build_path = project.root_path / owner.build_file.path
        self._writer.remove_managed_dependency(build_path, group_id, artifact_id)

        return self.infer_structure(project.root_path)

    def remove_direct_dependency(
        self, project: Project, module_name: str, group_id: str, artifact_id: str
    ) -> Project:
        target = find_module(project.root_module, module_name)
        if target is None:
            raise ValueError(f"Modulo '{module_name}' nao encontrado no projeto")

        build_path = project.root_path / target.build_file.path
        if not self._writer.remove_dependency(build_path, group_id, artifact_id):
            raise ValueError(
                f"Dependencia direta '{group_id}:{artifact_id}' nao encontrada em "
                f"'{target.name}'"
            )

        return self.infer_structure(project.root_path)

    def register_directory_role(
        self,
        project: Project,
        module_name: str,
        relative_path: Path,
        role: DirectoryRole,
    ) -> Project:
        raise NotImplementedError(
            _STUB_MESSAGE.format(method="register_directory_role")
        )

    def unregister_directory_role(
        self,
        project: Project,
        module_name: str,
        relative_path: Path,
        role: DirectoryRole,
    ) -> Project:
        raise NotImplementedError(
            _STUB_MESSAGE.format(method="unregister_directory_role")
        )


def _packaging_from_plugins(parsed: ParsedGradleBuild) -> str:
    if parsed.is_platform:
        return "pom"
    if parsed.has_java_plugin:
        return "jar"
    return "pom"
