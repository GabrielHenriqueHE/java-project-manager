from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, ListView, Static

from manager.adapters.base import BuildToolAdapter, DependentModuleConflict
from manager.models import BuildFile, Dependency, Module, Project, ProjectMetadata
from manager.screens.create_project import CreateProjectScreen
from manager.screens.export_manifest import ExportManifestScreen
from manager.screens.import_project import ImportProjectScreen
from manager.screens.widgets.app_header import AppHeader
from manager.screens.widgets.bom_panel import BomPanel
from manager.screens.widgets.build_source_form import BuildSourceFormScreen
from manager.screens.widgets.command_bar import CommandBar
from manager.screens.widgets.confirm_dialog import ConfirmModal
from manager.screens.widgets.dependency_form import DependencyFormScreen
from manager.screens.widgets.directory_form import DirectoryFormScreen
from manager.screens.widgets.metadata_form import MetadataFormScreen
from manager.screens.widgets.metadata_panel import MetadataPanel
from manager.screens.widgets.module_form import ModuleFormScreen
from manager.screens.widgets.modules_panel import ModulesPanel
from manager.screens.widgets.panel import Panel
from manager.screens.widgets.projects_panel import ProjectsPanel
from manager.screens.widgets.structure_panel import StructurePanel
from manager.services.adapters_registry import detect_adapter
from manager.services.registry import ProjectRegistry, RegistryEntry


class MainScreen(Screen):
    """Tela unica com os 5 paineis do layout 'mvnforge' (ver specs/design/tui-layout.md)."""

    BINDINGS = [
        ("1", "focus_panel(1)", "painel 1"),
        ("2", "focus_panel(2)", "painel 2"),
        ("3", "focus_panel(3)", "painel 3"),
        ("4", "focus_panel(4)", "painel 4"),
        ("5", "focus_panel(5)", "painel 5"),
        (":", "toggle_command_mode", "comando"),
    ]

    DEFAULT_CSS = """
    MainScreen #columns {
        height: 1fr;
    }

    MainScreen #col-1 {
        width: 16%;
    }

    MainScreen #col-2 {
        width: 40%;
    }

    MainScreen StructurePanel {
        width: 44%;
    }

    MainScreen ProjectsPanel {
        height: 2fr;
    }

    MainScreen ModulesPanel {
        height: 1fr;
    }

    MainScreen MetadataPanel {
        height: 1fr;
    }

    MainScreen BomPanel {
        height: 2fr;
    }

    MainScreen #footer-bar {
        height: 1;
    }

    MainScreen #panel-badge {
        width: auto;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    """

    def __init__(self, registry: ProjectRegistry | None = None):
        super().__init__()
        self.registry = registry or ProjectRegistry()
        self.project: Project | None = None
        self.selected_module: Module | None = None
        self._adapter: BuildToolAdapter | None = None

    def compose(self) -> ComposeResult:
        yield AppHeader()
        with Horizontal(id="columns"):
            with Vertical(id="col-1"):
                yield ProjectsPanel()
                yield ModulesPanel()
            with Vertical(id="col-2"):
                yield MetadataPanel()
                yield BomPanel()
            yield StructurePanel()
        with Horizontal(id="footer-bar"):
            yield Static("PAINEL 1", id="panel-badge")
            yield Footer()
        yield CommandBar(id="command-bar")

    def on_mount(self) -> None:
        self._reload_projects()

    # ---- estado / propagacao ----

    def _reload_projects(self) -> None:
        entries = self.registry.load()
        active_path = self.project.root_path if self.project else None
        self.query_one(ProjectsPanel).refresh_projects(entries, active_path)

    def _refresh_all_panels(self) -> None:
        self.query_one(ModulesPanel).refresh_modules(self.project, self.selected_module)
        self.query_one(MetadataPanel).refresh_module(self.selected_module)
        self.query_one(BomPanel).refresh_bom(self.project)
        self.query_one(StructurePanel).refresh_structure(self.project)
        self.query_one(AppHeader).set_project(self.project)

    def set_project(self, project: Project) -> None:
        self.project = project
        self.selected_module = project.root_module
        self._reload_projects()
        self._refresh_all_panels()

    # ---- acoes chamadas pelos paineis ----

    def import_project(self) -> None:
        def _on_dismiss(imported: bool | None) -> None:
            if not imported:
                return
            self._reload_projects()
            if self.project is None:
                entries = self.registry.load()
                if entries:
                    self.select_project(entries[-1])

        self.app.push_screen(ImportProjectScreen(self.registry), _on_dismiss)

    def create_project(self) -> None:
        def _on_dismiss(created: bool | None) -> None:
            if not created:
                return
            self._reload_projects()
            entries = self.registry.load()
            if entries:
                self.select_project(entries[-1])

        self.app.push_screen(CreateProjectScreen(self.registry), _on_dismiss)

    def export_project(self) -> None:
        if self.project is None:
            self.notify("Nenhum projeto selecionado", severity="error")
            return
        self.app.push_screen(ExportManifestScreen(self.project))

    def remove_project(self, entry: RegistryEntry | None) -> None:
        if entry is None:
            return
        self.registry.remove(entry.path)
        if self.project is not None and self.project.root_path == entry.path:
            self.project = None
            self.selected_module = None
            self._adapter = None
            self._refresh_all_panels()
        self._reload_projects()

    def select_project(self, entry: RegistryEntry) -> None:
        if self.project is not None and self.project.root_path == entry.path:
            return
        adapter = detect_adapter(entry.path)
        if adapter is None:
            self.notify(
                f"Nao foi possivel detectar a build tool em {entry.path}",
                severity="error",
            )
            return
        try:
            project = adapter.infer_structure(entry.path)
        except Exception as exc:
            self.notify(f"Falha ao inferir estrutura: {exc}", severity="error")
            return
        self._adapter = adapter
        self.set_project(project)

    def select_module(self, module: Module) -> None:
        self.selected_module = module
        self.query_one(MetadataPanel).refresh_module(module)

    def add_module(self, parent: Module | None) -> None:
        if self.project is None or self._adapter is None:
            self.notify("Nenhum projeto selecionado", severity="error")
            return
        parent_module = parent or self.project.root_module

        def _on_submit(module: Module | None) -> None:
            if module is None:
                return
            try:
                updated = self._adapter.add_module(
                    self.project, module, parent_name=parent_module.name
                )
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return
            self.notify(f"Modulo '{module.name}' criado")
            self.set_project(updated)

        self.app.push_screen(ModuleFormScreen(), _on_submit)

    def remove_module(self, module: Module) -> None:
        if self.project is None or self._adapter is None:
            return

        def _do_remove(force: bool) -> None:
            try:
                updated = self._adapter.remove_module(
                    self.project, module.name, force=force
                )
            except DependentModuleConflict as conflict:
                dependents = ", ".join(conflict.dependents)
                message = (
                    f"'{module.name}' e dependencia de: {dependents}.\n"
                    "Remover mesmo assim (as dependencias correspondentes tambem serao removidas)?"
                )

                def _on_confirm(confirmed: bool | None) -> None:
                    if confirmed:
                        _do_remove(force=True)

                self.app.push_screen(ConfirmModal(message), _on_confirm)
                return
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return

            self.notify("Modulo removido")
            self.set_project(updated)

        _do_remove(force=False)

    def update_metadata(self, module: Module) -> None:
        if self.project is None or self._adapter is None:
            self.notify("Nenhum projeto selecionado", severity="error")
            return

        def _on_submit(metadata: ProjectMetadata | None) -> None:
            if metadata is None:
                return
            try:
                updated = self._adapter.update_metadata(
                    self.project, module.name, metadata
                )
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return
            self.notify("Metadados atualizados")
            self.set_project(updated)

        self.app.push_screen(MetadataFormScreen(module), _on_submit)

    def add_dependency(self) -> None:
        if self.project is None or self._adapter is None:
            self.notify("Nenhum projeto selecionado", severity="error")
            return
        target_module = self.selected_module or self.project.root_module

        def _on_submit(dependency: Dependency | None) -> None:
            if dependency is None:
                return
            try:
                updated = self._adapter.update_dependency(
                    self.project, target_module.name, dependency
                )
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return
            self.notify(f"Dependencia '{dependency.artifact_id}' registrada")
            self.set_project(updated)

        self.app.push_screen(DependencyFormScreen(), _on_submit)

    def remove_dependency(self, dependency: Dependency) -> None:
        if self.project is None or self._adapter is None:
            self.notify("Nenhum projeto selecionado", severity="error")
            return
        try:
            updated = self._adapter.remove_dependency(
                self.project, dependency.group_id, dependency.artifact_id
            )
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return
        self.notify(f"Dependencia '{dependency.artifact_id}' removida")
        self.set_project(updated)

    def add_directory(self, module: Module, relative_path: str) -> None:
        if self.project is None or self._adapter is None:
            self.notify("Nenhum projeto selecionado", severity="error")
            return
        try:
            updated = self._adapter.add_directory(
                self.project, module.name, Path(relative_path)
            )
        except ValueError as exc:
            severity = "warning" if "ja existe" in str(exc) else "error"
            self.notify(str(exc), severity=severity)
            return
        self.notify(f"'{relative_path}' criado")
        self.set_project(updated)

    def add_custom_directory(self, module: Module) -> None:
        if self.project is None or self._adapter is None:
            self.notify("Nenhum projeto selecionado", severity="error")
            return

        def _on_submit(relative_path: str | None) -> None:
            if relative_path is None:
                return
            self.add_directory(module, relative_path)

        self.app.push_screen(DirectoryFormScreen(), _on_submit)

    def remove_directory(self, module: Module, relative_path: str) -> None:
        if self.project is None or self._adapter is None:
            self.notify("Nenhum projeto selecionado", severity="error")
            return
        try:
            updated = self._adapter.remove_directory(
                self.project, module.name, Path(relative_path)
            )
        except ValueError as exc:
            severity = "warning" if "nao existe" in str(exc) else "error"
            self.notify(str(exc), severity=severity)
            return
        self.notify(f"'{relative_path}' removido")
        self.set_project(updated)

    def register_build_source(self, module: Module) -> None:
        if self.project is None or self._adapter is None:
            self.notify("Nenhum projeto selecionado", severity="error")
            return

        def _on_submit(result: tuple[str, str] | None) -> None:
            if result is None:
                return
            relative_path, role = result
            try:
                updated = self._adapter.register_directory_role(
                    self.project, module.name, Path(relative_path), role
                )
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return
            self.notify(f"'{relative_path}' registrado como {role} no build")
            self.set_project(updated)

        self.app.push_screen(BuildSourceFormScreen(), _on_submit)

    # ---- navegacao entre paineis ----

    def action_focus_panel(self, number: int) -> None:
        for panel in self.query(Panel):
            if panel.panel_number == number:
                panel.focus_default()
                return

    def on_descendant_focus(self, event: events.DescendantFocus) -> None:
        node = event.widget
        while node is not None and not isinstance(node, Panel):
            node = node.parent
        if isinstance(node, Panel):
            self.query_one("#panel-badge", Static).update(f"PAINEL {node.panel_number}")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        list_view = event.list_view
        if list_view.id == "projects-list":
            entry = self.query_one(ProjectsPanel).selected_entry(list_view.index)
            if entry is not None:
                self.select_project(entry)
        elif list_view.id == "modules-list":
            module = self.query_one(ModulesPanel).module_at(list_view.index)
            if module is not None:
                self.select_module(module)

    # ---- modo comando ----

    def action_toggle_command_mode(self) -> None:
        bar = self.query_one(CommandBar)
        footer_bar = self.query_one("#footer-bar")
        context = self.selected_module.name if self.selected_module else "-"
        bar.placeholder = f":comando em {context} (modulo <nome>) > digite e pressione enter · esc cancela"
        bar.value = ""
        footer_bar.display = False
        bar.display = True
        bar.focus()

    def cancel_command(self) -> None:
        self._close_command_bar()

    def run_command(self, text: str) -> None:
        self._close_command_bar()
        text = text.strip()
        if not text:
            return

        parts = text.split(maxsplit=1)
        command, argument = parts[0], (parts[1].strip() if len(parts) > 1 else "")

        if command == "modulo" and argument:
            self._quick_add_module(argument)
        else:
            self.notify(
                f"Comando nao reconhecido ou nao implementado: {text}",
                severity="warning",
            )

    def _quick_add_module(self, artifact_id: str) -> None:
        if self.project is None or self._adapter is None:
            self.notify("Nenhum projeto selecionado", severity="error")
            return

        parent = self.selected_module or self.project.root_module
        module = Module(
            name=artifact_id,
            relative_path=Path(artifact_id),
            metadata=ProjectMetadata(artifact_id=artifact_id),
            build_file=BuildFile(path=Path(artifact_id) / "pom.xml"),
        )
        try:
            updated = self._adapter.add_module(
                self.project, module, parent_name=parent.name
            )
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return
        self.notify(f"Modulo '{artifact_id}' criado")
        self.set_project(updated)

    def _close_command_bar(self) -> None:
        bar = self.query_one(CommandBar)
        footer_bar = self.query_one("#footer-bar")
        bar.display = False
        footer_bar.display = True
