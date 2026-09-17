from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class RemoveDependencyFormScreen(ModalScreen[tuple[str, str] | None]):
    """Formulario minimo (groupId + artifactId) para identificar qual
    dependencia direta remover de um modulo - sem version/type/scope,
    irrelevantes para uma remocao (diferente de DependencyFormScreen, que
    coleta esses campos para criar/editar).
    """

    def __init__(self, *, title: str = "Remover dependencia direta") -> None:
        super().__init__()
        self._title = title

    DEFAULT_CSS = """
    RemoveDependencyFormScreen {
        align: center middle;
    }

    RemoveDependencyFormScreen > Vertical {
        width: 64;
        height: auto;
        padding: 1 2;
        border: thick $primary;
        background: $surface;
    }

    RemoveDependencyFormScreen Input {
        margin-bottom: 1;
    }

    RemoveDependencyFormScreen #form-feedback {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static(self._title),
            Label("groupId *"),
            Input(id="field-group-id"),
            Label("artifactId *"),
            Input(id="field-artifact-id"),
            Static(id="form-feedback"),
            Button("Remover", id="form-confirm", variant="primary"),
            Button("Cancelar", id="form-cancel"),
        )

    @on(Button.Pressed, "#form-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#form-confirm")
    def _confirm(self) -> None:
        group_id = self.query_one("#field-group-id", Input).value.strip()
        artifact_id = self.query_one("#field-artifact-id", Input).value.strip()
        feedback = self.query_one("#form-feedback", Static)

        if not group_id or not artifact_id:
            feedback.update("[red]Informe groupId e artifactId.[/red]")
            return

        self.dismiss((group_id, artifact_id))
