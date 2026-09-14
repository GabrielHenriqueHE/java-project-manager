from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmModal(ModalScreen[bool]):
    """Dialogo generico de confirmacao, usado antes de acoes destrutivas."""

    DEFAULT_CSS = """
    ConfirmModal {
        align: center middle;
    }

    ConfirmModal > Grid {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 1 2;
        width: 60;
        height: 11;
        border: thick $primary;
        background: $surface;
    }

    ConfirmModal > Grid > Static {
        column-span: 2;
        content-align: center middle;
    }
    """

    def __init__(
        self,
        message: str,
        *,
        confirm_label: str = "Confirmar",
        cancel_label: str = "Cancelar",
    ):
        super().__init__()
        self._message = message
        self._confirm_label = confirm_label
        self._cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        yield Grid(
            Static(self._message, id="confirm-message"),
            Button(self._cancel_label, id="confirm-no", variant="primary"),
            Button(self._confirm_label, id="confirm-yes", variant="error"),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-yes")
