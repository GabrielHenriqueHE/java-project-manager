from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView, Static

from manager.models import Dependency, Module, Project
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
        ("m", "add_direct_dependency", "dep. direta"),
        ("j", "cursor_down", "mover"),
        ("k", "cursor_up", "mover"),
        ("d", "remove_dependency", "remover"),
    ]

    def __init__(self, **kwargs):
        super().__init__(4, "BOM + DEPENDENCIAS", **kwargs)
        self._dependencies: list[Dependency] = []

    def compose_body(self) -> ComposeResult:
        yield Static(
            "nada declarado. pressione n", id="bom-empty", classes="panel-empty-state"
        )
        yield ListView(id="bom-list")
        yield Static(id="direct-deps-header")
        yield Static(id="direct-deps-list")

    def on_mount(self) -> None:
        self.refresh_bom(None)

    def refresh_bom(
        self, project: Project | None, selected_module: Module | None = None
    ) -> None:
        list_view = self.query_one("#bom-list", ListView)
        empty = self.query_one("#bom-empty", Static)
        list_view.clear()
        self._dependencies = []

        if project is None:
            self.set_header_right("")
            empty.update("nenhum projeto selecionado")
            empty.display = True
            list_view.display = False
            self._render_direct_dependencies(None)
            return

        bom_module = find_bom_module(project.root_module)
        self.set_header_right(bom_module.name if bom_module else "-")

        dependencies = project.managed_dependencies
        if not dependencies:
            empty.update("nada declarado. pressione n")
            empty.display = True
            list_view.display = False
        else:
            empty.display = False
            list_view.display = True
            self._dependencies = dependencies
            for dep in dependencies:
                scope = dep.scope or "import"
                list_view.append(
                    ListItem(
                        Label(
                            f"bom {dep.group_id}:[bold]{dep.artifact_id}[/] {dep.version} · [dim]{scope}[/]"
                        )
                    )
                )
            list_view.index = 0

        self._render_direct_dependencies(selected_module)

    def _render_direct_dependencies(self, selected_module: Module | None) -> None:
        header = self.query_one("#direct-deps-header", Static)
        body = self.query_one("#direct-deps-list", Static)

        if selected_module is None:
            header.update("")
            body.update("")
            return

        header.update(f"diretas de {selected_module.name} (m adiciona)")
        direct = [dep for dep in selected_module.dependencies if not dep.managed]
        if not direct:
            body.update("[dim]nenhuma dependencia direta[/]")
            return

        lines = []
        for dep in direct:
            version = dep.version or "-"
            scope = dep.scope or "compile"
            lines.append(
                f"{dep.group_id}:[bold]{dep.artifact_id}[/] {version} · [dim]{scope}[/]"
            )
        body.update("\n".join(lines))

    def focus_default(self) -> None:
        self.query_one("#bom-list", ListView).focus()

    def action_cursor_down(self) -> None:
        self.query_one("#bom-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#bom-list", ListView).action_cursor_up()

    def action_add_dependency(self) -> None:
        self.screen.add_dependency()

    def action_add_direct_dependency(self) -> None:
        self.screen.add_direct_dependency()

    def dependency_at(self, index: int | None) -> Dependency | None:
        if index is not None and 0 <= index < len(self._dependencies):
            return self._dependencies[index]
        return None

    def action_remove_dependency(self) -> None:
        index = self.query_one("#bom-list", ListView).index
        dependency = self.dependency_at(index)
        if dependency is not None:
            self.screen.remove_dependency(dependency)
