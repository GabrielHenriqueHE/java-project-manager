from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, Tree

from manager.models import Module, Project
from manager.screens.widgets.project_tree import ProjectTree


class ProjectDetailScreen(Screen):
    """Mostra a arvore de modulos de um projeto inferido, em modo leitura."""

    BINDINGS = [("escape", "app.pop_screen", "Voltar")]

    def __init__(self, project: Project):
        super().__init__()
        self._project = project

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            ProjectTree(self._project, id="project-tree"),
            Static(id="module-details", classes="module-details"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self._show_module(self._project.root_module)

    def on_tree_node_selected(self, event: Tree.NodeSelected[Module]) -> None:
        module = event.node.data
        if module is not None:
            self._show_module(module)

    def _show_module(self, module: Module) -> None:
        meta = module.metadata
        directory = module.directory_structure
        lines = [
            f"[b]{module.name}[/b]{'  [BOM]' if module.is_bom else ''}",
            "",
            f"groupId: {meta.group_id or '-'}",
            f"artifactId: {meta.artifact_id}",
            f"version: {meta.version or '-'}",
            f"packaging: {meta.packaging}",
            f"description: {meta.description or '-'}",
            "",
            f"[b]Estrutura de diretorios[/b] ({directory.convention})",
            f"  source: {', '.join(directory.source_dirs) or '-'}",
            f"  test: {', '.join(directory.test_dirs) or '-'}",
            f"  resources: {', '.join(directory.resource_dirs) or '-'}",
            "",
            "[b]Dependencias[/b]",
        ]
        if module.dependencies:
            for dep in module.dependencies:
                tag = " (gerenciada)" if dep.managed else ""
                version = dep.version or "-"
                lines.append(f"  {dep.group_id}:{dep.artifact_id}:{version}{tag}")
        else:
            lines.append("  (nenhuma)")

        self.query_one("#module-details", Static).update("\n".join(lines))
