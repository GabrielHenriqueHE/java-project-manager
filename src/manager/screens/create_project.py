from pathlib import Path

import yaml
from pydantic import ValidationError
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from manager.adapters.maven.adapter import MavenAdapter
from manager.manifest import load_manifest
from manager.models import Module
from manager.services.registry import ProjectRegistry


def _count_modules(module: Module) -> int:
    return 1 + sum(_count_modules(sub) for sub in module.submodules)


class CreateProjectScreen(Screen[bool]):
    """Pede um manifesto YAML + diretorio de destino e materializa um projeto novo.

    So MavenAdapter e usado aqui (sem deteccao de build tool, ja que ainda
    nao ha nenhum pom.xml em disco para detectar a partir dele).
    """

    BINDINGS = [("escape", "app.pop_screen", "Cancelar")]

    def __init__(self, registry: ProjectRegistry | None = None):
        super().__init__()
        self._registry = registry or ProjectRegistry()
        self._adapter = MavenAdapter()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Informe o path do manifesto YAML:"),
            Input(placeholder="/caminho/para/manifest.yaml", id="manifest-input"),
            Static("Informe o diretorio de destino:"),
            Input(placeholder="/caminho/para/o/novo-projeto", id="destination-input"),
            Static(id="create-feedback"),
            Button("Criar", id="confirm-create", variant="primary"),
            id="create-form",
        )
        yield Footer()

    @on(Input.Submitted)
    def _submit_via_enter(self) -> None:
        self._do_create()

    @on(Button.Pressed, "#confirm-create")
    def _submit_via_button(self) -> None:
        self._do_create()

    def _do_create(self) -> None:
        raw_manifest_path = self.query_one("#manifest-input", Input).value.strip()
        raw_destination = self.query_one("#destination-input", Input).value.strip()
        feedback = self.query_one("#create-feedback", Static)

        if not raw_manifest_path or not raw_destination:
            feedback.update("[red]Informe o manifesto e o destino.[/red]")
            return

        manifest_path = Path(raw_manifest_path).expanduser()
        if not manifest_path.is_file():
            feedback.update(f"[red]Manifesto nao encontrado: {manifest_path}[/red]")
            return

        try:
            manifest = load_manifest(manifest_path)
        except yaml.YAMLError as exc:
            feedback.update(f"[red]YAML invalido: {exc}[/red]")
            return
        except ValidationError as exc:
            feedback.update(f"[red]Manifesto invalido: {exc}[/red]")
            return

        destination = Path(raw_destination).expanduser()
        files_dir = manifest_path.parent / f"{manifest_path.stem}.files"
        source_root = files_dir if files_dir.is_dir() else None
        try:
            project = self._adapter.create_project(
                manifest, destination, source_root=source_root
            )
        except ValueError as exc:
            feedback.update(f"[red]{exc}[/red]")
            return

        self._registry.add(destination.resolve(), self._adapter.build_tool)
        total_modules = _count_modules(project.root_module)
        feedback.update(
            f"[green]Criado: {project.name} ({total_modules} modulos)[/green]"
        )
        self.set_timer(0.6, self._finish)

    def _finish(self) -> None:
        self.dismiss(True)
