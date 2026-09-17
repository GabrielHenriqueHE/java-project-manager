from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from manager.models import Module
from manager.services.adapters_registry import detect_adapter
from manager.services.git import GitCloneError, clone_repository
from manager.services.registry import ProjectRegistry


def _count_modules(module: Module) -> int:
    return 1 + sum(_count_modules(sub) for sub in module.submodules)


class CloneProjectScreen(Screen[bool]):
    """Clona um repositorio remoto via git e registra o projeto resultante.

    Depois do clone, segue exatamente o mesmo fluxo de ImportProjectScreen
    a partir de um path ja existente em disco (detect_adapter ->
    infer_structure -> ProjectRegistry.add).
    """

    BINDINGS = [("escape", "app.pop_screen", "Cancelar")]

    def __init__(self, registry: ProjectRegistry | None = None):
        super().__init__()
        self._registry = registry or ProjectRegistry()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Clonar repositorio remoto:"),
            Static("URL do repositorio"),
            Input(
                placeholder="https://github.com/usuario/projeto.git", id="url-input"
            ),
            Static("Path de destino"),
            Input(placeholder="/caminho/para/o/projeto", id="dest-input"),
            Static(id="clone-feedback"),
            Button("Clonar", id="confirm-clone", variant="primary"),
            id="clone-form",
        )
        yield Footer()

    @on(Button.Pressed, "#confirm-clone")
    def _submit_via_button(self) -> None:
        self._do_clone()

    def _do_clone(self) -> None:
        url = self.query_one("#url-input", Input).value.strip()
        raw_dest = self.query_one("#dest-input", Input).value.strip()
        feedback = self.query_one("#clone-feedback", Static)

        if not url or not raw_dest:
            feedback.update("[red]Informe a URL e o path de destino.[/red]")
            return

        destination = Path(raw_dest).expanduser()

        try:
            clone_repository(url, destination)
        except GitCloneError as exc:
            feedback.update(f"[red]{exc}[/red]")
            return

        adapter = detect_adapter(destination)
        if adapter is None:
            feedback.update(
                f"[yellow]Clonado, mas nenhuma build tool reconhecida em "
                f"{destination}[/yellow]"
            )
            return

        try:
            project = adapter.infer_structure(destination)
        except Exception as exc:
            feedback.update(f"[red]Clonado, mas falha ao inferir estrutura: {exc}[/red]")
            return

        self._registry.add(destination, adapter.build_tool)
        total_modules = _count_modules(project.root_module)
        feedback.update(
            f"[green]Clonado e importado: {project.name} ({total_modules} modulos)[/green]"
        )
        self.set_timer(0.6, self._finish)

    def _finish(self) -> None:
        self.dismiss(True)
