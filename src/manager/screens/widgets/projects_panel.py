from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView, Static

from manager.screens.widgets.panel import Panel
from manager.services.registry import RegistryEntry


class ProjectsPanel(Panel):
    """Painel [1] PROJETOS: lista de projetos registrados."""

    can_focus = False

    BINDINGS = [
        ("n", "import_project", "novo"),
        ("i", "init_project", "iniciar"),
        ("c", "create_project", "criar"),
        ("g", "clone_project", "clonar"),
        ("e", "export_project", "exportar"),
        ("d", "remove_project", "remover"),
        ("j", "cursor_down", "mover"),
        ("k", "cursor_up", "mover"),
    ]

    def __init__(self, **kwargs):
        super().__init__(1, "PROJETOS", **kwargs)
        self._entries: list[RegistryEntry] = []

    def compose_body(self) -> ComposeResult:
        yield Static("carregando…", id="projects-empty", classes="panel-empty-state")
        yield ListView(id="projects-list")

    def on_mount(self) -> None:
        self.refresh_projects([], None)

    def refresh_projects(
        self, entries: list[RegistryEntry], active_path: Path | None
    ) -> None:
        self._entries = entries
        list_view = self.query_one("#projects-list", ListView)
        empty = self.query_one("#projects-empty", Static)

        list_view.clear()
        self.set_header_right(f"{len(entries)} repos")

        if not entries:
            empty.display = True
            list_view.display = False
            return

        empty.display = False
        list_view.display = True
        active_index = 0
        for index, entry in enumerate(entries):
            is_active = entry.path == active_path
            if is_active:
                active_index = index
            marker = "●" if is_active else "○"
            list_view.append(
                ListItem(
                    Label(f"{marker} {entry.path.name}  [dim]{entry.build_tool}[/]")
                )
            )
        list_view.index = active_index

    def focus_default(self) -> None:
        self.query_one("#projects-list", ListView).focus()

    def selected_entry(self, index: int | None) -> RegistryEntry | None:
        if index is not None and 0 <= index < len(self._entries):
            return self._entries[index]
        return None

    def action_cursor_down(self) -> None:
        self.query_one("#projects-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#projects-list", ListView).action_cursor_up()

    def action_import_project(self) -> None:
        self.screen.import_project()

    def action_init_project(self) -> None:
        self.screen.init_project()

    def action_create_project(self) -> None:
        self.screen.create_project()

    def action_clone_project(self) -> None:
        self.screen.clone_project()

    def action_export_project(self) -> None:
        self.screen.export_project()

    def action_remove_project(self) -> None:
        index = self.query_one("#projects-list", ListView).index
        self.screen.remove_project(self.selected_entry(index))
