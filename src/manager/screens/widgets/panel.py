from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static


class Panel(Vertical):
    """Painel numerado reutilizavel: header '[n] TITULO' + texto dinamico a
    direita + corpo definido pela subclasse via compose_body().

    Por padrao o proprio painel e focavel (usado pelos paineis sem um widget
    interno naturalmente focavel, ex.: Metadados/Estrutura). Paineis baseados
    em ListView devem definir can_focus = False e delegar o foco ao ListView
    via focus_default().
    """

    can_focus = True

    DEFAULT_CSS = """
    Panel {
        border: round $primary;
        padding: 0 1;
        height: 1fr;
    }

    Panel:focus {
        border: round $accent;
    }

    Panel > .panel-header {
        height: 1;
        margin-bottom: 1;
    }

    Panel .panel-title {
        width: auto;
        color: $accent;
        text-style: bold;
    }

    Panel .panel-header-right {
        width: 1fr;
        text-align: right;
        color: $text-muted;
    }

    Panel .panel-empty-state {
        color: $text-muted;
    }
    """

    def __init__(self, number: int, title: str, **kwargs):
        super().__init__(**kwargs)
        self.panel_number = number
        self.panel_title = title

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static(f"[{self.panel_number}] {self.panel_title}", classes="panel-title"),
            Static("", classes="panel-header-right", id="panel-header-right"),
            classes="panel-header",
        )
        yield from self.compose_body()

    def compose_body(self) -> ComposeResult:
        yield from ()

    def set_header_right(self, text: str) -> None:
        self.query_one("#panel-header-right", Static).update(text)

    def focus_default(self) -> None:
        self.focus()
