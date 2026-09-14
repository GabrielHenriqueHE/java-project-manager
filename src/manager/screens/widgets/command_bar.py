from textual.widgets import Input


class CommandBar(Input):
    """Substitui o footer quando o modo comando (':') esta ativo."""

    BINDINGS = [("escape", "cancel", "cancelar")]

    DEFAULT_CSS = """
    CommandBar {
        display: none;
        border: none;
        height: 1;
        background: $panel;
    }
    """

    def action_cancel(self) -> None:
        self.screen.cancel_command()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.screen.run_command(event.value)
