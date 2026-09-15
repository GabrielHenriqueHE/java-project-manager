from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView, Static

from manager.models import Module, Project
from manager.screens.widgets.panel import Panel


def find_bom_module(module: Module) -> Module | None:
    if module.is_bom:
        return module
    for sub in module.submodules:
        found = find_bom_module(sub)
        if found is not None:
            return found
    return None


class BomPanel(Panel):
    """Painel [4] BOM + DEPENDENCIAS: dependencias gerenciadas do projeto."""

    can_focus = False

    BINDINGS = [
        ("n", "add_dependency", "novo"),
        ("j", "cursor_down", "mover"),
        ("k", "cursor_up", "mover"),
    ]

    def __init__(self, **kwargs):
        super().__init__(4, "BOM + DEPENDENCIAS", **kwargs)

    def compose_body(self) -> ComposeResult:
        yield Static(
            "nada declarado. pressione n", id="bom-empty", classes="panel-empty-state"
        )
        yield ListView(id="bom-list")

    def on_mount(self) -> None:
        self.refresh_bom(None)

    def refresh_bom(self, project: Project | None) -> None:
        list_view = self.query_one("#bom-list", ListView)
        empty = self.query_one("#bom-empty", Static)
        list_view.clear()

        if project is None:
            self.set_header_right("")
            empty.update("nenhum projeto selecionado")
            empty.display = True
            list_view.display = False
            return

        bom_module = find_bom_module(project.root_module)
        self.set_header_right(bom_module.name if bom_module else "-")

        dependencies = project.managed_dependencies
        if not dependencies:
            empty.update("nada declarado. pressione n")
            empty.display = True
            list_view.display = False
            return

        empty.display = False
        list_view.display = True
        for dep in dependencies:
            scope = dep.scope or "import"
            list_view.append(
                ListItem(
                    Label(
                        f"bom {dep.group_id}:[bold]{dep.artifact_id}[/] {dep.version} · [dim]{scope}[/]"
                    )
                )
            )

    def focus_default(self) -> None:
        self.query_one("#bom-list", ListView).focus()

    def action_cursor_down(self) -> None:
        self.query_one("#bom-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#bom-list", ListView).action_cursor_up()

    def action_add_dependency(self) -> None:
        self.screen.add_dependency()
