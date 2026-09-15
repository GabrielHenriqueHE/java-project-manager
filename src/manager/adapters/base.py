from abc import ABC, abstractmethod
from pathlib import Path

from manager.models import BuildTool, Dependency, Module, Project, ProjectMetadata


class DependentModuleConflict(Exception):
    """Levantado quando remover/alterar um modulo quebraria dependencias de outros modulos."""

    def __init__(self, module_name: str, dependents: list[str]):
        self.module_name = module_name
        self.dependents = dependents
        super().__init__(
            f"Modulo '{module_name}' e dependencia de: {', '.join(dependents)}"
        )


class BuildToolAdapter(ABC):
    build_tool: BuildTool

    @abstractmethod
    def detect(self, root_path: Path) -> bool:
        """Retorna True se este adapter sabe lidar com o projeto em root_path."""

    @abstractmethod
    def infer_structure(self, root_path: Path) -> Project:
        """Le os arquivos de build reais e monta o modelo de dominio."""

    @abstractmethod
    def add_module(
        self, project: Project, module: Module, *, parent_name: str | None = None
    ) -> Project:
        """Cria o novo modulo em disco e atualiza os pom(s) pai(is) envolvidos."""

    @abstractmethod
    def remove_module(
        self, project: Project, module_name: str, *, force: bool = False
    ) -> Project:
        """Remove o modulo, a entrada no BOM se houver, e valida dependentes.

        Levanta DependentModuleConflict se force=False e houver modulos que
        dependem do removido.
        """

    @abstractmethod
    def update_dependency(
        self, project: Project, module_name: str, dependency: Dependency
    ) -> Project:
        """Adiciona/atualiza uma dependencia (ou entrada gerenciada se dependency.managed)."""

    @abstractmethod
    def update_metadata(
        self, project: Project, module_name: str, metadata: ProjectMetadata
    ) -> Project:
        """Atualiza os metadados de um modulo."""

    @abstractmethod
    def add_directory(
        self, project: Project, module_name: str, relative_path: Path
    ) -> Project:
        """Cria relative_path (relativo a raiz do modulo) em disco.

        Levanta ValueError se o modulo nao existir, se o diretorio ja
        existir, ou se relative_path escapar do diretorio do modulo.
        """

    @abstractmethod
    def remove_directory(
        self, project: Project, module_name: str, relative_path: Path
    ) -> Project:
        """Remove relative_path (relativo a raiz do modulo) do disco, se vazio.

        Levanta ValueError se o modulo nao existir, se relative_path
        escapar do diretorio do modulo, se o diretorio nao existir, ou
        se nao estiver vazio. Nunca remove recursivamente.
        """

    @abstractmethod
    def remove_dependency(
        self, project: Project, group_id: str, artifact_id: str
    ) -> Project:
        """Remove a dependencia gerenciada (managed=True) identificada por
        (group_id, artifact_id), em qualquer modulo do projeto que a declare.

        Levanta ValueError se nenhum modulo tiver essa dependencia gerenciada.
        """
