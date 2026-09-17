from pathlib import Path

from pydantic import ValidationError
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Static

from manager.adapters.base import BuildToolAdapter
from manager.adapters.gradle.adapter import GradleAdapter
from manager.adapters.maven.adapter import MavenAdapter
from manager.manifest import ModuleManifest
from manager.models import ProjectMetadata
from manager.services.registry import ProjectRegistry

_VALID_BUILD_TOOLS = {"maven", "gradle"}


class InitProjectScreen(Screen[bool]):
    """Pede os dados de um projeto novo (sem manifesto) e materializa via
    BuildToolAdapter.create_project, com um unico modulo raiz (sem
    submodulos/BOM/dependencias - fora de escopo desta fatia).
    """

    BINDINGS = [("escape", "app.pop_screen", "Cancelar")]

    def __init__(self, registry: ProjectRegistry | None = None):
        super().__init__()
        self._registry = registry or ProjectRegistry()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static("Build tool (maven ou gradle):"),
            Input(placeholder="maven", id="field-build-tool"),
            Static("Group ID (opcional para Gradle; obrigatorio para Maven):"),
            Input(placeholder="com.example", id="field-group-id"),
            Static("Artifact ID:"),
            Input(placeholder="meu-projeto", id="field-artifact-id"),
            Static("Version (opcional para Gradle; obrigatorio para Maven):"),
            Input(placeholder="1.0.0", id="field-version"),
            Static("Diretorio de destino:"),
            Input(placeholder="/caminho/para/o/novo-projeto", id="field-destination"),
            Static(id="init-feedback"),
            Button("Criar", id="confirm-init", variant="primary"),
            id="init-form",
        )
        yield Footer()

    @on(Input.Submitted)
    def _submit_via_enter(self) -> None:
        self._do_create()

    @on(Button.Pressed, "#confirm-init")
    def _submit_via_button(self) -> None:
        self._do_create()

    def _do_create(self) -> None:
        feedback = self.query_one("#init-feedback", Static)

        build_tool = self.query_one("#field-build-tool", Input).value.strip().lower()
        artifact_id = self.query_one("#field-artifact-id", Input).value.strip()
        raw_destination = self.query_one("#field-destination", Input).value.strip()

        if build_tool not in _VALID_BUILD_TOOLS:
            feedback.update("[red]Informe a build tool: 'maven' ou 'gradle'.[/red]")
            return
        if not artifact_id:
            feedback.update("[red]Informe o artifactId.[/red]")
            return
        if not raw_destination:
            feedback.update("[red]Informe o diretorio de destino.[/red]")
            return

        group_id = self.query_one("#field-group-id", Input).value.strip() or None
        version = self.query_one("#field-version", Input).value.strip() or None
        destination = Path(raw_destination).expanduser()

        try:
            manifest = ModuleManifest(
                metadata=ProjectMetadata(
                    group_id=group_id,
                    artifact_id=artifact_id,
                    version=version,
                    packaging="jar",
                ),
            )
        except ValidationError as exc:
            feedback.update(f"[red]Dados invalidos: {exc}[/red]")
            return

        adapter: BuildToolAdapter = (
            MavenAdapter() if build_tool == "maven" else GradleAdapter()
        )

        try:
            project = adapter.create_project(manifest, destination)
        except ValueError as exc:
            feedback.update(f"[red]{exc}[/red]")
            return

        self._registry.add(destination.resolve(), adapter.build_tool)
        feedback.update(f"[green]Criado: {project.name} (1 modulo)[/green]")
        self.set_timer(0.6, self._finish)

    def _finish(self) -> None:
        self.dismiss(True)
