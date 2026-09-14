from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from manager.models import Module, Project


class ProjectTree(Tree[Module]):
    """Arvore que renderiza recursivamente os submodulos de um Project."""

    def __init__(
        self,
        project: Project,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        super().__init__(
            project.name,
            data=project.root_module,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self._project = project

    def on_mount(self) -> None:
        self._populate(self.root, self._project.root_module)
        self.root.expand()

    def _populate(self, node: TreeNode[Module], module: Module) -> None:
        node.data = module
        for submodule in module.submodules:
            label = submodule.name + (" [BOM]" if submodule.is_bom else "")
            child = node.add(label, data=submodule, expand=True)
            self._populate(child, submodule)
