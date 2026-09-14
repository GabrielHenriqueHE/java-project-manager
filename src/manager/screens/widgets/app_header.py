from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from manager.models import Module, Project


def count_modules(module: Module) -> int:
    return 1 + sum(count_modules(sub) for sub in module.submodules)


def count_direct_dependencies(module: Module) -> int:
    direct = sum(1 for dep in module.dependencies if not dep.managed)
    return direct + sum(count_direct_dependencies(sub) for sub in module.submodules)


class AppHeader(Horizontal):
    """Cabecalho customizado: coordenada Maven a esquerda, contadores a direita."""

    DEFAULT_CSS = """
    AppHeader {
        height: 1;
        background: $panel;
        padding: 0 1;
    }

    AppHeader #header-left {
        width: 1fr;
    }

    AppHeader #header-right {
        width: auto;
        text-align: right;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold $accent]mvnforge[/]", id="header-left")
        yield Static("", id="header-right")

    def set_project(self, project: Project | None) -> None:
        left = self.query_one("#header-left", Static)
        right = self.query_one("#header-right", Static)

        if project is None:
            left.update("[bold $accent]mvnforge[/]")
            right.update("")
            return

        meta = project.root_module.metadata
        coordinate = f"{meta.group_id or '?'}:{meta.artifact_id}:{meta.version or '?'}"
        left.update(f"[bold $accent]mvnforge[/] {coordinate}")

        java_version = meta.properties.get("maven.compiler.source", "?")
        n_mod = count_modules(project.root_module)
        n_dep = count_direct_dependencies(project.root_module)
        right.update(f"java {java_version} · maven · {n_mod} mod · {n_dep} dep")
