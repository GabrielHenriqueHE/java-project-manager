from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class DuplicateModuleFormScreen(ModalScreen[dict | None]):
    """Formulario para coletar o nome do novo modulo ao duplicar source_name.

    Devolve via dismiss() um dict {"new_name": str, "group_id": str | None,
    "version": str | None} - group_id/version ficam None (herdam do modulo
    fonte) quando deixados em branco.
    """

    DEFAULT_CSS = """
    DuplicateModuleFormScreen {
        align: center middle;
    }

    DuplicateModuleFormScreen > Vertical {
        width: 64;
        height: auto;
        padding: 1 2;
        border: thick $primary;
        background: $surface;
    }

    DuplicateModuleFormScreen Input {
        margin-bottom: 1;
    }

    DuplicateModuleFormScreen #form-feedback {
        margin-bottom: 1;
    }
    """

    def __init__(self, source_name: str):
        super().__init__()
        self._source_name = source_name

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static(f"Duplicar '{self._source_name}' para..."),
            Label("Nome (artifactId) do novo modulo *"),
            Input(placeholder="ex.: utils-copy", id="field-new-name"),
            Label("groupId (opcional - vazio = herda do modulo fonte)"),
            Input(id="field-group-id"),
            Label("version (opcional - vazio = herda do modulo fonte)"),
            Input(id="field-version"),
            Static(id="form-feedback"),
            Button("Duplicar", id="form-confirm", variant="primary"),
            Button("Cancelar", id="form-cancel"),
        )

    @on(Button.Pressed, "#form-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#form-confirm")
    def _confirm(self) -> None:
        new_name = self.query_one("#field-new-name", Input).value.strip()
        feedback = self.query_one("#form-feedback", Static)
        if not new_name:
            feedback.update("[red]Informe o nome do novo modulo.[/red]")
            return

        group_id = self.query_one("#field-group-id", Input).value.strip() or None
        version = self.query_one("#field-version", Input).value.strip() or None

        self.dismiss(
            {"new_name": new_name, "group_id": group_id, "version": version}
        )
