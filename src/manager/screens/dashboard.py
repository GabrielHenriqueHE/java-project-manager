from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from manager.services.adapters_registry import detect_adapter
from manager.services.registry import ProjectRegistry, RegistryEntry


class DashboardScreen(Screen):
    """Lista os projetos conhecidos e permite importar/abrir/remover."""

    BINDINGS = [
        ("i", "import_project", "Importar"),
        ("d", "remove_selected", "Remover"),
    ]

    def __init__(self, registry: ProjectRegistry | None = None):
        super().__init__()
        self._registry = registry or ProjectRegistry()
        self._entries: list[RegistryEntry] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Projetos registrados — [i] importar, [enter] abrir, [d] remover"),
            DataTable(id="projects-table"),
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#projects-table", DataTable)
        table.add_columns("Nome", "Build tool", "Path")
        table.cursor_type = "row"
        self._reload()

    def _reload(self) -> None:
        table = self.query_one("#projects-table", DataTable)
        table.clear()
        self._entries = self._registry.load()
        for entry in self._entries:
            name = (
                entry.path.name
                if entry.path.is_dir()
                else f"{entry.path.name} (indisponivel)"
            )
            table.add_row(name, entry.build_tool, str(entry.path))

    def action_import_project(self) -> None:
        from manager.screens.import_project import ImportProjectScreen

        def _on_dismiss(imported: bool | None) -> None:
            if imported:
                self._reload()

        self.app.push_screen(ImportProjectScreen(self._registry), _on_dismiss)

    def _selected_entry(self) -> RegistryEntry | None:
        table = self.query_one("#projects-table", DataTable)
        if table.cursor_row is None or not self._entries:
            return None
        if table.cursor_row >= len(self._entries):
            return None
        return self._entries[table.cursor_row]

    def action_remove_selected(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        self._registry.remove(entry.path)
        self._reload()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self._open_entry_at(event.cursor_row)

    def _open_entry_at(self, row_index: int) -> None:
        if row_index >= len(self._entries):
            return
        entry = self._entries[row_index]

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

        from manager.screens.project_detail import ProjectDetailScreen

        self.app.push_screen(ProjectDetailScreen(project))
