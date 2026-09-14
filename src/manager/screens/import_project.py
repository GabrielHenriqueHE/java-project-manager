from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from manager.models import Module
from manager.services.adapters_registry import detect_adapter
from manager.services.registry import ProjectRegistry


def _count_modules(module: Module) -> int:
    return 1 + sum(_count_modules(sub) for sub in module.submodules)


class ImportProjectScreen(Screen[bool]):
    """Pede um path de projeto Java existente, infere a estrutura e registra."""

    BINDINGS = [("escape", "app.pop_screen", "Cancelar")]

    def __init__(self, registry: ProjectRegistry | None = None):
        super().__init__()
        self._registry = registry or ProjectRegistry()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Informe o path do projeto Java a importar:"),
            Input(placeholder="/caminho/para/o/projeto", id="path-input"),
            Static(id="import-feedback"),
            Button("Importar", id="confirm-import", variant="primary"),
            id="import-form",
        )
        yield Footer()

    @on(Input.Submitted, "#path-input")
    def _submit_via_enter(self) -> None:
        self._do_import()

    @on(Button.Pressed, "#confirm-import")
    def _submit_via_button(self) -> None:
        self._do_import()

    def _do_import(self) -> None:
        raw_path = self.query_one("#path-input", Input).value.strip()
        feedback = self.query_one("#import-feedback", Static)
        if not raw_path:
            feedback.update("[red]Informe um path.[/red]")
            return

        path = Path(raw_path).expanduser()
        if not path.is_dir():
            feedback.update(f"[red]Path nao encontrado: {path}[/red]")
            return

        adapter = detect_adapter(path)
        if adapter is None:
            feedback.update(f"[red]Nenhuma build tool reconhecida em {path}[/red]")
            return

        try:
            project = adapter.infer_structure(path)
        except Exception as exc:
            feedback.update(f"[red]Falha ao inferir estrutura: {exc}[/red]")
            return

        self._registry.add(path, adapter.build_tool)
        total_modules = _count_modules(project.root_module)
        feedback.update(
            f"[green]Importado: {project.name} ({total_modules} modulos)[/green]"
        )
        self.set_timer(0.6, self._finish)

    def _finish(self) -> None:
        self.dismiss(True)
