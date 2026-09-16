from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from manager.manifest import dump_manifest, to_manifest
from manager.models import Project


class ExportManifestScreen(Screen[bool]):
    """Pede um path de destino e exporta o projeto ja carregado para manifesto YAML.

    So serializa o Project ja em memoria (nenhuma leitura de disco/adapter
    novo) - inverso de CreateProjectScreen.
    """

    BINDINGS = [("escape", "app.pop_screen", "Cancelar")]

    def __init__(self, project: Project):
        super().__init__()
        self._project = project

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static(f"Exportar '{self._project.name}' para:"),
            Input(placeholder="/caminho/para/manifest.yaml", id="destination-input"),
            Static(id="export-feedback"),
            Button("Exportar", id="confirm-export", variant="primary"),
            id="export-form",
        )
        yield Footer()

    @on(Input.Submitted, "#destination-input")
    def _submit_via_enter(self) -> None:
        self._do_export()

    @on(Button.Pressed, "#confirm-export")
    def _submit_via_button(self) -> None:
        self._do_export()

    def _do_export(self) -> None:
        raw_path = self.query_one("#destination-input", Input).value.strip()
        feedback = self.query_one("#export-feedback", Static)
        if not raw_path:
            feedback.update("[red]Informe o caminho de destino.[/red]")
            return

        path = Path(raw_path).expanduser()
        manifest = to_manifest(self._project.root_module)
        try:
            dump_manifest(manifest, path)
        except OSError as exc:
            feedback.update(f"[red]Falha ao exportar: {exc}[/red]")
            return

        feedback.update(f"[green]Exportado para {path}[/green]")
        self.set_timer(0.6, self._finish)

    def _finish(self) -> None:
        self.dismiss(True)
