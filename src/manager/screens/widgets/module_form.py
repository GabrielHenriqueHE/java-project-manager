from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from manager.models import BuildFile, Module, ProjectMetadata


class ModuleFormScreen(ModalScreen[Module | None]):
    """Formulario para coletar os dados de um novo modulo a ser criado.

    Devolve um Module "rascunho" via dismiss() - apenas metadata e
    dependencies sao usados pelo adapter; os demais campos (relative_path,
    build_file, directory_structure) sao placeholders recalculados na
    inferencia apos a criacao real do modulo.
    """

    DEFAULT_CSS = """
    ModuleFormScreen {
        align: center middle;
    }

    ModuleFormScreen > Vertical {
        width: 64;
        height: auto;
        padding: 1 2;
        border: thick $primary;
        background: $surface;
    }

    ModuleFormScreen Input {
        margin-bottom: 1;
    }

    ModuleFormScreen #form-feedback {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Novo modulo"),
            Label("Nome (artifactId) *"),
            Input(placeholder="ex.: utils", id="field-artifact-id"),
            Label("groupId (vazio = herda do pai)"),
            Input(id="field-group-id"),
            Label("version (vazio = herda do pai)"),
            Input(id="field-version"),
            Label("packaging"),
            Input(value="jar", id="field-packaging"),
            Label("name"),
            Input(id="field-name"),
            Label("description"),
            Input(id="field-description"),
            Static(id="form-feedback"),
            Button("Criar", id="form-confirm", variant="primary"),
            Button("Cancelar", id="form-cancel"),
        )

    @on(Button.Pressed, "#form-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#form-confirm")
    def _confirm(self) -> None:
        artifact_id = self.query_one("#field-artifact-id", Input).value.strip()
        feedback = self.query_one("#form-feedback", Static)
        if not artifact_id:
            feedback.update("[red]Informe o nome (artifactId).[/red]")
            return

        group_id = self.query_one("#field-group-id", Input).value.strip() or None
        version = self.query_one("#field-version", Input).value.strip() or None
        packaging = self.query_one("#field-packaging", Input).value.strip() or "jar"
        name = self.query_one("#field-name", Input).value.strip() or None
        description = self.query_one("#field-description", Input).value.strip() or None

        module = Module(
            name=artifact_id,
            relative_path=Path(artifact_id),
            metadata=ProjectMetadata(
                artifact_id=artifact_id,
                group_id=group_id,
                version=version,
                packaging=packaging,
                name=name,
                description=description,
            ),
            build_file=BuildFile(path=Path(artifact_id) / "pom.xml"),
        )
        self.dismiss(module)
