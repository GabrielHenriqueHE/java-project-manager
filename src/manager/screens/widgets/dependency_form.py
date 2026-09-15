from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from manager.models import Dependency


class DependencyFormScreen(ModalScreen[Dependency | None]):
    """Formulario para declarar uma dependencia gerenciada (BOM).

    Usado apenas pelo Painel [4] BOM + DEPENDENCIAS - a dependencia
    resultante e sempre `managed=True` (ver specs/phases/phase-2-update-dependency:
    editar dependencias diretas de um modulo qualquer fica fora desta fatia).
    """

    DEFAULT_CSS = """
    DependencyFormScreen {
        align: center middle;
    }

    DependencyFormScreen > Vertical {
        width: 64;
        height: auto;
        padding: 1 2;
        border: thick $primary;
        background: $surface;
    }

    DependencyFormScreen Input {
        margin-bottom: 1;
    }

    DependencyFormScreen #form-feedback {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Nova dependencia gerenciada (BOM)"),
            Label("groupId *"),
            Input(id="field-group-id"),
            Label("artifactId *"),
            Input(id="field-artifact-id"),
            Label("version *"),
            Input(id="field-version"),
            Label("type (ex.: pom, para importar outro BOM)"),
            Input(id="field-type"),
            Label("scope (ex.: import)"),
            Input(id="field-scope"),
            Static(id="form-feedback"),
            Button("Salvar", id="form-confirm", variant="primary"),
            Button("Cancelar", id="form-cancel"),
        )

    @on(Button.Pressed, "#form-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#form-confirm")
    def _confirm(self) -> None:
        group_id = self.query_one("#field-group-id", Input).value.strip()
        artifact_id = self.query_one("#field-artifact-id", Input).value.strip()
        version = self.query_one("#field-version", Input).value.strip()
        feedback = self.query_one("#form-feedback", Static)

        if not group_id or not artifact_id or not version:
            feedback.update("[red]Informe groupId, artifactId e version.[/red]")
            return

        type_ = self.query_one("#field-type", Input).value.strip() or None
        scope = self.query_one("#field-scope", Input).value.strip() or None

        dependency = Dependency(
            group_id=group_id,
            artifact_id=artifact_id,
            version=version,
            type=type_,
            scope=scope,
            managed=True,
        )
        self.dismiss(dependency)
