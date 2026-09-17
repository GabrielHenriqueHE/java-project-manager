from pathlib import Path

from manager.adapters.base import BuildToolAdapter
from manager.adapters.gradle.directory import detect_directory_structure
from manager.adapters.gradle.parser import (
    ParsedGradleBuild,
    ParsedSettings,
    find_build_file,
    find_settings_file,
    parse_build_file,
    parse_settings_file,
)
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
    """Suporte de leitura a projetos Gradle (Groovy e Kotlin DSL).

    Fase 15 (fundacao): so `detect`/`infer_structure`. Mutacoes (criar
    projeto, adicionar/remover modulo, dependencias, diretorios) sao
    stubs `NotImplementedError` - mesmo padrao usado pelo MavenAdapter na
    sua Fase 1, antes das mutacoes reais chegarem em fatias seguintes.
    """

    build_tool = "gradle"

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
        raise NotImplementedError(_STUB_MESSAGE.format(method="add_module"))

    def remove_module(
        self, project: Project, module_name: str, *, force: bool = False
    ) -> Project:
        raise NotImplementedError(_STUB_MESSAGE.format(method="remove_module"))

    def update_dependency(
        self, project: Project, module_name: str, dependency: Dependency
    ) -> Project:
        raise NotImplementedError(_STUB_MESSAGE.format(method="update_dependency"))

    def update_metadata(
        self, project: Project, module_name: str, metadata: ProjectMetadata
    ) -> Project:
        raise NotImplementedError(_STUB_MESSAGE.format(method="update_metadata"))

    def add_directory(
        self, project: Project, module_name: str, relative_path: Path
    ) -> Project:
        raise NotImplementedError(_STUB_MESSAGE.format(method="add_directory"))

    def remove_directory(
        self,
        project: Project,
        module_name: str,
        relative_path: Path,
        *,
        force: bool = False,
    ) -> Project:
        raise NotImplementedError(_STUB_MESSAGE.format(method="remove_directory"))

    def remove_dependency(
        self, project: Project, group_id: str, artifact_id: str
    ) -> Project:
        raise NotImplementedError(_STUB_MESSAGE.format(method="remove_dependency"))

    def remove_direct_dependency(
        self, project: Project, module_name: str, group_id: str, artifact_id: str
    ) -> Project:
        raise NotImplementedError(
            _STUB_MESSAGE.format(method="remove_direct_dependency")
        )

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
