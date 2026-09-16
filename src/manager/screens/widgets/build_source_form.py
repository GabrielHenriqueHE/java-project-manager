from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

_VALID_ROLES = {"source", "test-source", "resource", "test-resource"}


class BuildSourceFormScreen(ModalScreen[tuple[str, str] | None]):
    """Formulario para registrar um diretorio como fonte/recurso extra no
    build (via build-helper-maven-plugin) - dois campos: caminho e role.

    Nao cria o diretorio nem verifica se ele existe (isso e feito pelo
    adapter); este form so coleta os dois valores.
    """

    DEFAULT_CSS = """
    BuildSourceFormScreen {
        align: center middle;
    }

    BuildSourceFormScreen > Vertical {
        width: 64;
        height: auto;
        padding: 1 2;
        border: thick $primary;
        background: $surface;
    }

    BuildSourceFormScreen Input {
        margin-bottom: 1;
    }

    BuildSourceFormScreen #form-feedback {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Registrar diretorio no build"),
            Static("Caminho relativo ao modulo"),
            Input(placeholder="ex.: src/main/proto", id="field-path"),
            Static("Role (source, test-source, resource ou test-resource)"),
            Input(placeholder="source", id="field-role"),
            Static(id="form-feedback"),
            Button("Registrar", id="form-confirm", variant="primary"),
            Button("Cancelar", id="form-cancel"),
        )

    @on(Button.Pressed, "#form-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#form-confirm")
    def _confirm(self) -> None:
        path = self.query_one("#field-path", Input).value.strip()
        role = self.query_one("#field-role", Input).value.strip()
        feedback = self.query_one("#form-feedback", Static)

        if not path or not role:
            feedback.update("[red]Informe o caminho e o role.[/red]")
            return
        if role not in _VALID_ROLES:
            feedback.update(
                f"[red]Role invalido. Use um de: {', '.join(sorted(_VALID_ROLES))}.[/red]"
            )
            return

        self.dismiss((path, role))
