from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, Tree

from manager.adapters.base import DependentModuleConflict
from manager.models import Module, Project
from manager.screens.widgets.confirm_dialog import ConfirmModal
from manager.screens.widgets.module_form import ModuleFormScreen
from manager.screens.widgets.project_tree import ProjectTree
from manager.services.adapters_registry import detect_adapter


class ProjectDetailScreen(Screen):
    """Mostra a arvore de modulos de um projeto inferido.

    Leitura de metadados/dependencias/estrutura de diretorios; remocao de
    modulo e a unica mutacao suportada nesta fase.
    """

    BINDINGS = [
        ("escape", "app.pop_screen", "Voltar"),
        ("a", "add_module", "Adicionar modulo"),
        ("r", "remove_selected_module", "Remover modulo"),
    ]

    def __init__(self, project: Project):
        super().__init__()
        self._project = project
        self._selected_module: Module = project.root_module

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
            self._selected_module = module
            self._show_module(module)

    def action_add_module(self) -> None:
        parent = self._selected_module
        adapter = detect_adapter(self._project.root_path)
        if adapter is None:
            self.notify(
                "Nao foi possivel detectar a build tool do projeto", severity="error"
            )
            return

        def _on_submit(module: Module | None) -> None:
            if module is None:
                return
            try:
                updated = adapter.add_module(
                    self._project, module, parent_name=parent.name
                )
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return
            self._apply_updated_project(
                updated, message=f"Modulo '{module.name}' criado"
            )

        self.app.push_screen(ModuleFormScreen(), _on_submit)

    def action_remove_selected_module(self) -> None:
        module_name = self._selected_module.name
        adapter = detect_adapter(self._project.root_path)
        if adapter is None:
            self.notify(
                "Nao foi possivel detectar a build tool do projeto", severity="error"
            )
            return

        try:
            updated = adapter.remove_module(self._project, module_name)
        except DependentModuleConflict as conflict:
            dependents = ", ".join(conflict.dependents)
            message = (
                f"'{module_name}' e dependencia de: {dependents}.\n"
                "Remover mesmo assim (as dependencias correspondentes tambem serao removidas)?"
            )

            def _on_confirm(confirmed: bool | None) -> None:
                if confirmed:
                    self._force_remove(adapter, module_name)

            self.app.push_screen(ConfirmModal(message), _on_confirm)
            return
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return

        self._apply_updated_project(updated, message="Modulo removido")

    def _force_remove(self, adapter, module_name: str) -> None:
        try:
            updated = adapter.remove_module(self._project, module_name, force=True)
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return
        self._apply_updated_project(updated, message="Modulo removido")

    def _apply_updated_project(self, updated: Project, *, message: str) -> None:
        self._project = updated
        self._selected_module = updated.root_module
        self.query_one("#project-tree", ProjectTree).refresh_project(updated)
        self._show_module(updated.root_module)
        self.notify(message)

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
