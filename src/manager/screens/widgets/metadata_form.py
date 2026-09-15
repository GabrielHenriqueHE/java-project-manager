from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from manager.models import Module, ProjectMetadata


class MetadataFormScreen(ModalScreen[ProjectMetadata | None]):
    """Formulario para editar os metadados de um modulo existente.

    artifactId e mostrado como texto somente-leitura - renomear um modulo
    exigiria mover o diretorio em disco e atualizar o pom pai/dependentes,
    fora do escopo desta fatia (ver specs/phases/phase-2-update-metadata).
    """

    DEFAULT_CSS = """
    MetadataFormScreen {
        align: center middle;
    }

    MetadataFormScreen > Vertical {
        width: 64;
        height: auto;
        padding: 1 2;
        border: thick $primary;
        background: $surface;
    }

    MetadataFormScreen Input {
        margin-bottom: 1;
    }

    MetadataFormScreen #form-feedback {
        margin-bottom: 1;
    }
    """

    def __init__(self, module: Module, **kwargs):
        super().__init__(**kwargs)
        self._module = module

    def compose(self) -> ComposeResult:
        meta = self._module.metadata
        java_version = meta.properties.get("maven.compiler.source", "")
        yield Vertical(
            Static(f"Editar metadados — {meta.artifact_id}"),
            Label("artifactId (somente leitura)"),
            Static(meta.artifact_id, id="field-artifact-id-readonly"),
            Label("name"),
            Input(value=meta.name or "", id="field-name"),
            Label("groupId (vazio = herda do pai, quando houver)"),
            Input(value=meta.group_id or "", id="field-group-id"),
            Label("version (vazio = herda do pai, quando houver)"),
            Input(value=meta.version or "", id="field-version"),
            Label("java.version"),
            Input(value=java_version, id="field-java-version"),
            Label("packaging"),
            Input(value=meta.packaging, id="field-packaging"),
            Label("description"),
            Input(value=meta.description or "", id="field-description"),
            Static(id="form-feedback"),
            Button("Salvar", id="form-confirm", variant="primary"),
            Button("Cancelar", id="form-cancel"),
        )

    @on(Button.Pressed, "#form-cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#form-confirm")
    def _confirm(self) -> None:
        packaging = self.query_one("#field-packaging", Input).value.strip()
        feedback = self.query_one("#form-feedback", Static)
        if not packaging:
            feedback.update("[red]Informe o packaging.[/red]")
            return

        group_id = self.query_one("#field-group-id", Input).value.strip() or None
        version = self.query_one("#field-version", Input).value.strip() or None
        name = self.query_one("#field-name", Input).value.strip() or None
        description = self.query_one("#field-description", Input).value.strip() or None
        java_version = self.query_one("#field-java-version", Input).value.strip()
        properties = {"maven.compiler.source": java_version} if java_version else {}

        metadata = ProjectMetadata(
            artifact_id=self._module.metadata.artifact_id,
            group_id=group_id,
            version=version,
            name=name,
            description=description,
            packaging=packaging,
            properties=properties,
        )
        self.dismiss(metadata)
