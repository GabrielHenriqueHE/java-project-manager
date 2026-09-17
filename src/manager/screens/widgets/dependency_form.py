from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from manager.models import Dependency


class DependencyFormScreen(ModalScreen[Dependency | None]):
    """Formulario para declarar uma dependencia gerenciada (BOM) ou uma
    dependencia direta de um modulo - o par de operacoes usa o mesmo
    formulario, so title/managed mudam (ver phase-12-dependencia-direta).

    version e obrigatoria apenas para `managed=True`: uma dependencia
    direta pode depender de uma version vinda do dependencyManagement,
    entao fica opcional - mesma regra ja aplicada por
    MavenAdapter.update_dependency.
    """

    def __init__(
        self,
        *,
        title: str = "Nova dependencia gerenciada (BOM)",
        managed: bool = True,
    ) -> None:
        super().__init__()
        self._title = title
        self._managed = managed

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
        version_label = "version *" if self._managed else "version (opcional)"
        type_hint = (
            "type (ex.: pom, para importar outro BOM)"
            if self._managed
            else "type (ex.: pom, jar, ...)"
        )
        scope_hint = (
            "scope (ex.: import)"
            if self._managed
            else "scope (ex.: compile, provided, runtime, test)"
        )
        yield Vertical(
            Static(self._title),
            Label("groupId *"),
            Input(id="field-group-id"),
            Label("artifactId *"),
            Input(id="field-artifact-id"),
            Label(version_label),
            Input(id="field-version"),
            Label(type_hint),
            Input(id="field-type"),
            Label(scope_hint),
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
        version = self.query_one("#field-version", Input).value.strip() or None
        feedback = self.query_one("#form-feedback", Static)

        if not group_id or not artifact_id:
            feedback.update("[red]Informe groupId e artifactId.[/red]")
            return
        if self._managed and not version:
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
            managed=self._managed,
        )
        self.dismiss(dependency)
