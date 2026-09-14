from dataclasses import dataclass, field
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from manager.models import Module, Project
from manager.screens.widgets.panel import Panel

_CHECKLIST_DIRS = [
    "src/main/java",
    "src/main/resources",
    "src/test/java",
    "src/test/resources",
    "src/main/webapp",
    "src/main/proto",
    "src/it/java",
    "docs",
]


def _flatten_modules(module: Module) -> list[Module]:
    result = [module]
    for sub in module.submodules:
        result.extend(_flatten_modules(sub))
    return result


def _collapse_single_child_dirs(path: Path) -> str:
    """Colapsa uma cadeia de diretorios com exatamente um filho (diretorio) e
    nenhum arquivo em 'a/b/c/', parando ao encontrar ramificacao ou arquivos."""
    parts: list[str] = []
    current = path
    while current.is_dir():
        entries = list(current.iterdir())
        dirs = [e for e in entries if e.is_dir()]
        files = [e for e in entries if e.is_file()]
        if len(dirs) == 1 and not files:
            parts.append(dirs[0].name)
            current = dirs[0]
        else:
            break
    return "/".join(parts) + "/" if parts else ""


@dataclass
class _TreeNode:
    text: str
    children: list["_TreeNode"] = field(default_factory=list)


def _build_module_node(module: Module, root_path: Path, is_root: bool) -> _TreeNode:
    module_dir = root_path / module.relative_path
    is_pom = module.metadata.packaging == "pom"

    if is_root:
        node = _TreeNode("pom.xml" + (" (packaging: pom)" if is_pom else ""))
    else:
        node = _TreeNode(f"{module.name}/")
        node.children.append(
            _TreeNode("pom.xml" + (" (packaging: pom)" if is_pom else ""))
        )

    dirs = module.directory_structure
    for rel in [
        *dirs.source_dirs,
        *dirs.resource_dirs,
        *dirs.test_dirs,
        *dirs.test_resource_dirs,
    ]:
        abs_dir = module_dir / rel
        if not abs_dir.is_dir():
            continue
        dir_node = _TreeNode(f"{rel}/")
        collapsed = _collapse_single_child_dirs(abs_dir)
        if collapsed:
            dir_node.children.append(_TreeNode(collapsed))
        node.children.append(dir_node)

    for sub in module.submodules:
        node.children.append(_build_module_node(sub, root_path, is_root=False))

    return node


def _render_tree(node: _TreeNode, prefix: str = "", is_root: bool = True) -> list[str]:
    lines = [node.text] if is_root else []
    children = node.children
    for index, child in enumerate(children):
        is_last = index == len(children) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{child.text}")
        extension = "    " if is_last else "│   "
        lines.extend(_render_tree(child, prefix + extension, is_root=False))
    return lines


def render_project_tree(project: Project) -> str:
    root_node = _build_module_node(project.root_module, project.root_path, is_root=True)
    return "\n".join(_render_tree(root_node))


class StructurePanel(Panel):
    """Painel [5] ESTRUTURA: checklist de diretorios + arvore do projeto."""

    BINDINGS = [("space", "toggle_active_module", "alterna")]

    def __init__(self, **kwargs):
        super().__init__(5, "ESTRUTURA", **kwargs)
        self._project: Project | None = None
        self._modules: list[Module] = []
        self._active_index = 0

    def compose_body(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(id="structure-checklist")
            yield Static(id="structure-tree")

    def on_mount(self) -> None:
        self.refresh_structure(None)

    def refresh_structure(self, project: Project | None) -> None:
        self._project = project
        checklist = self.query_one("#structure-checklist", Static)
        tree = self.query_one("#structure-tree", Static)

        if project is None:
            self._modules = []
            self._active_index = 0
            self.set_header_right("")
            checklist.update("")
            tree.update("sem modulos. pressione n")
            return

        self._modules = _flatten_modules(project.root_module)
        self._active_index = min(self._active_index, len(self._modules) - 1)
        self._render_checklist()
        tree.update(render_project_tree(project))

    def _render_checklist(self) -> None:
        checklist = self.query_one("#structure-checklist", Static)
        if not self._project or not self._modules:
            checklist.update("")
            self.set_header_right("")
            return

        active_module = self._modules[self._active_index]
        module_dir = self._project.root_path / active_module.relative_path
        self.set_header_right(f"space alterna · {active_module.name}")

        lines = []
        for rel in _CHECKLIST_DIRS:
            checked = (module_dir / rel).is_dir()
            box = "[bold $accent][x][/]" if checked else "[dim][ ][/]"
            style = "" if checked else "[dim]"
            close = "" if checked else "[/]"
            lines.append(f"{box} {style}{rel}{close}")
        checklist.update("\n".join(lines))

    def action_toggle_active_module(self) -> None:
        if not self._modules:
            return
        self._active_index = (self._active_index + 1) % len(self._modules)
        self._render_checklist()
