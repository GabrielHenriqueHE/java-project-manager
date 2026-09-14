from textual.app import ComposeResult
from textual.widgets import Static

from manager.models import Module
from manager.screens.widgets.panel import Panel

_LABEL_WIDTH = 14


class MetadataPanel(Panel):
    """Painel [2] METADADOS: tabela chave-valor do modulo selecionado."""

    BINDINGS = [("enter", "edit", "edita")]

    def __init__(self, **kwargs):
        super().__init__(2, "METADADOS", **kwargs)

    def compose_body(self) -> ComposeResult:
        yield Static(
            "nenhum projeto selecionado",
            id="metadata-body",
            classes="panel-empty-state",
        )

    def on_mount(self) -> None:
        self.set_header_right("enter edita")
        self.refresh_module(None)

    def refresh_module(self, module: Module | None) -> None:
        body = self.query_one("#metadata-body", Static)
        if module is None:
            body.set_classes("panel-empty-state")
            body.update("nenhum projeto selecionado")
            return

        meta = module.metadata
        java_version = meta.properties.get("maven.compiler.source", "-")
        fields = [
            ("name", meta.name or "-"),
            ("groupId", meta.group_id or "-"),
            ("artifactId", meta.artifact_id),
            ("version", meta.version or "-"),
            ("java.version", java_version),
            ("packaging", meta.packaging),
            ("description", meta.description or "-"),
        ]
        lines = [
            f"[dim]{label:<{_LABEL_WIDTH}}[/] [bold]{value}[/]"
            for label, value in fields
        ]
        body.set_classes("")
        body.update("\n".join(lines))

    def action_edit(self) -> None:
        self.notify(
            "Edicao de metadados ainda nao implementada (Fase 2 seguinte)",
            severity="warning",
        )
