from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView, Static

from manager.models import Module, Project
from manager.screens.widgets.panel import Panel


def flatten_with_connectors(module: Module) -> list[tuple[str, Module]]:
    """Achata a arvore de modulos em pares (prefixo, modulo), com conectores
    estilo 'tree' (├─/└─) calculados pela posicao de cada modulo entre seus
    irmaos."""

    def _walk(node: Module, prefix: str) -> list[tuple[str, Module]]:
        result: list[tuple[str, Module]] = []
        children = node.submodules
        for index, child in enumerate(children):
            is_last = index == len(children) - 1
            connector = "└─ " if is_last else "├─ "
            result.append((prefix + connector, child))
            extension = "   " if is_last else "│  "
            result.extend(_walk(child, prefix + extension))
        return result

    return [("", module), *_walk(module, "")]


class ModulesPanel(Panel):
    """Painel [3] MODULOS: arvore de modulos do projeto ativo."""

    can_focus = False

    BINDINGS = [
        ("n", "add_module", "novo"),
        ("d", "remove_module", "remover"),
        ("j", "cursor_down", "mover"),
        ("k", "cursor_up", "mover"),
    ]

    def __init__(self, **kwargs):
        super().__init__(3, "MODULOS", **kwargs)
        self._modules: list[Module] = []

    def compose_body(self) -> ComposeResult:
        yield Static(
            "nenhum projeto selecionado",
            id="modules-empty",
            classes="panel-empty-state",
        )
        yield ListView(id="modules-list")

    def on_mount(self) -> None:
        self.refresh_modules(None, None)

    def refresh_modules(
        self, project: Project | None, active_module: Module | None
    ) -> None:
        list_view = self.query_one("#modules-list", ListView)
        empty = self.query_one("#modules-empty", Static)

        list_view.clear()
        self._modules = []

        if project is None:
            empty.update("nenhum projeto selecionado")
            empty.display = True
            list_view.display = False
            self.set_header_right("")
            return

        self.set_header_right(project.name)
        entries = flatten_with_connectors(project.root_module)
        active_index = 0
        for index, (prefix, module) in enumerate(entries):
            self._modules.append(module)
            if (
                active_module is not None
                and module.relative_path == active_module.relative_path
            ):
                active_index = index
            list_view.append(
                ListItem(
                    Label(f"{prefix}{module.name}  [dim]{module.metadata.packaging}[/]")
                )
            )

        empty.display = False
        list_view.display = True
        list_view.index = active_index

    def focus_default(self) -> None:
        self.query_one("#modules-list", ListView).focus()

    def module_at(self, index: int | None) -> Module | None:
        if index is not None and 0 <= index < len(self._modules):
            return self._modules[index]
        return None

    def action_cursor_down(self) -> None:
        self.query_one("#modules-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#modules-list", ListView).action_cursor_up()

    def action_add_module(self) -> None:
        index = self.query_one("#modules-list", ListView).index
        self.screen.add_module(self.module_at(index))

    def action_remove_module(self) -> None:
        index = self.query_one("#modules-list", ListView).index
        module = self.module_at(index)
        if module is not None:
            self.screen.remove_module(module)
