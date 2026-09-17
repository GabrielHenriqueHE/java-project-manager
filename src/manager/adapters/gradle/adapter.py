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
from manager.manifest import ModuleManifest, is_bom_manifest, validate_manifest_tree
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

    Fase 15 (fundacao): `detect`/`infer_structure`. Fases 16-23: as 9
    mutacoes que fazem sentido no modelo Gradle desta feature -
    diretorios, metadados, dependencias (upsert/remocao gerenciada e
    direta), modulos (adicionar/remover) e `create_project` - todas
    implementadas de ponta a ponta, reaproveitando `GradleWriter` para
    a edicao textual de `build.gradle(.kts)`/`settings.gradle(.kts)`.
    `register_directory_role`/`unregister_directory_role` continuam
    stub `NotImplementedError` - o mecanismo equivalente no Gradle
    (`sourceSets{}`) esta permanentemente fora de escopo desta feature
    (ver `specs/features/06-suporte-gradle/requirements.md`), nao e uma
    fatia pendente.
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

    # ---- mutacoes ----

    def create_project(
        self,
        manifest: ModuleManifest,
        destination_path: Path,
        *,
        source_root: Path | None = None,
    ) -> Project:
        validate_manifest_tree(manifest)
        self._validate_gradle_manifest(manifest)

        destination_path = destination_path.resolve()
        if destination_path.exists() and any(destination_path.iterdir()):
            raise ValueError(f"'{destination_path}' ja existe e nao esta vazio")
        destination_path.mkdir(parents=True, exist_ok=True)

        # O manifesto e agnostico de build tool (Fase 6) e nao carrega
        # nenhuma informacao de dialeto Gradle - create_project sempre
        # materializa em Groovy (build.gradle/settings.gradle). Decisao
        # deliberada e conservadora: adicionar um campo de dialeto ao
        # manifesto reabriria uma decisao de arquitetura da Fase 6, o
        # que nao foi pedido.
        root_artifact_id = manifest.metadata.artifact_id
        submodule_names = [sub.metadata.artifact_id for sub in manifest.submodules]

        settings_lines = [f"rootProject.name = '{root_artifact_id}'"]
        if submodule_names:
            includes = ", ".join(f"'{name}'" for name in submodule_names)
            settings_lines.append(f"include {includes}")
        (destination_path / "settings.gradle").write_text(
            "\n".join(settings_lines) + "\n"
        )

        self._writer.create_build_file(
            destination_path / "build.gradle",
            packaging=manifest.metadata.packaging,
            group_id=manifest.metadata.group_id,
            version=manifest.metadata.version,
            dependencies=manifest.dependencies,
        )
        self._materialize_directories(
            destination_path,
            manifest.directory_structure,
            source_root,
            root_artifact_id,
        )

        for sub in manifest.submodules:
            module_dir = destination_path / sub.metadata.artifact_id
            self._writer.create_build_file(
                module_dir / "build.gradle",
                packaging=sub.metadata.packaging,
                group_id=sub.metadata.group_id,
                version=sub.metadata.version,
                dependencies=sub.dependencies,
            )
            self._materialize_directories(
                module_dir,
                sub.directory_structure,
                source_root,
                sub.metadata.artifact_id,
            )

        return self.infer_structure(destination_path)

    def _validate_gradle_manifest(self, module: ModuleManifest) -> None:
        """Mesmas validacoes estruturais do Maven (`_validate_maven_manifest`),
        MENOS a exigencia de groupId/version no modulo raiz: essa regra
        existe no Maven porque o pom raiz nao tem <parent> de quem
        herdar; o Gradle nunca leu heranca nenhuma (nem de
        allprojects{}), entao group/version ausentes na raiz sao apenas
        omitidos do build.gradle, sem erro.
        """
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
            self._validate_gradle_manifest(sub)

    def _materialize_directories(
        self,
        module_dir: Path,
        structure,
        source_root: Path | None,
        artifact_id: str,
    ) -> None:
        """Cria (ou copia de `source_root`, se houver) os diretorios de
        `structure`. Ao contrario do Maven, nunca "registra" um
        diretorio nao-convencional no build - o equivalente Gradle
        (`sourceSets{}`) esta fora de escopo desta feature
        (`register_directory_role`/`unregister_directory_role`
        continuam stub); o diretorio e criado/copiado normalmente, so
        nao aparece com o sufixo `(build)` no Painel [5].
        """
        module_snapshot = (source_root / artifact_id) if source_root else None
        all_dirs = {
            *structure.source_dirs,
            *structure.test_dirs,
            *structure.resource_dirs,
            *structure.test_resource_dirs,
        }
        for rel_dir in all_dirs:
            target = module_dir / rel_dir
            snapshot = (module_snapshot / rel_dir) if module_snapshot else None
            if snapshot is not None and snapshot.is_dir():
                shutil.copytree(snapshot, target, dirs_exist_ok=True)
            else:
                target.mkdir(parents=True, exist_ok=True)

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

    # ---- fora de escopo: sourceSets{} nao implementado ----

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
