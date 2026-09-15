from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


class DirectoryFormScreen(ModalScreen[str | None]):
    """Formulario de caminho livre para criar um diretorio customizado.

    Reaproveita MainScreen.add_directory (mesma operacao ja usada pelo
    checklist fixo do Painel [5]) - este form so oferece uma segunda
    porta de entrada de UI, sem nenhuma mudanca no adapter.
    """

    DEFAULT_CSS = """
    DirectoryFormScreen {
        align: center middle;
    }

    DirectoryFormScreen > Vertical {
        width: 64;
        height: auto;
        padding: 1 2;
        border: thick $primary;
        background: $surface;
    }

    DirectoryFormScreen Input {
        margin-bottom: 1;
    }

    DirectoryFormScreen #form-feedback {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Novo diretorio"),
            Static("Caminho relativo ao modulo"),
            Input(placeholder="ex.: src/main/proto", id="field-path"),
            Static(id="form-feedback"),
            Button("Criar", id="form-confirm", variant="primary"),
            Button("Cancelar", id="form-cancel"),
        )

    @on(Button.Pressed, "#form-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#form-confirm")
    def _confirm(self) -> None:
        path = self.query_one("#field-path", Input).value.strip()
        feedback = self.query_one("#form-feedback", Static)
        if not path:
            feedback.update("[red]Informe o caminho.[/red]")
            return
        self.dismiss(path)
