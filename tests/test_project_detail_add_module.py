import shutil
from pathlib import Path

import pytest
from textual.app import App
from textual.widgets import Input, Tree

from manager.screens.dashboard import DashboardScreen
from manager.screens.project_detail import ProjectDetailScreen
from manager.services.registry import ProjectRegistry

FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "maven-multi-module"


@pytest.fixture
def project_root(tmp_path) -> Path:
    dest = tmp_path / "project"
    shutil.copytree(FIXTURE_SOURCE, dest)
    return dest


class _TestApp(App):
    def __init__(self, registry: ProjectRegistry):
        super().__init__()
        self._project_registry = registry

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen(self._project_registry))


def _module_names(detail: ProjectDetailScreen) -> set[str]:
    names = {detail._project.root_module.name}
    for sub in detail._project.root_module.submodules:
        names.add(sub.name)
    return names


async def test_add_module_under_root_creates_module_and_updates_tree(
    project_root, tmp_path
):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        detail = app.screen
        assert isinstance(detail, ProjectDetailScreen)
        assert detail._selected_module.name == detail._project.root_module.name

        await pilot.press("a")
        await pilot.pause()

        form = app.screen
        assert type(form).__name__ == "ModuleFormScreen"
        form.query_one("#field-artifact-id", Input).value = "utils"
        await pilot.click("#form-confirm")
        await pilot.pause()

        assert isinstance(app.screen, ProjectDetailScreen)
        assert "utils" in _module_names(detail)
        assert (project_root / "utils" / "src" / "main" / "java").is_dir()


async def test_add_module_cancelled_creates_nothing(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        detail = app.screen
        await pilot.press("a")
        await pilot.pause()
        await pilot.click("#form-cancel")
        await pilot.pause()

        assert isinstance(app.screen, ProjectDetailScreen)
        assert "utils" not in _module_names(detail)
        assert not (project_root / "utils").exists()


async def test_add_module_under_non_pom_parent_shows_error(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        detail = app.screen
        tree = detail.query_one("#project-tree", Tree)
        tree.focus()
        # root -> bom -> core
        await pilot.press("down", "down", "enter")
        await pilot.pause()
        assert detail._selected_module.name == "core"

        await pilot.press("a")
        await pilot.pause()
        form = app.screen
        form.query_one("#field-artifact-id", Input).value = "nested"
        await pilot.click("#form-confirm")
        await pilot.pause()

        # o form fecha e a tela de detalhe volta a aparecer, mesmo em erro
        assert isinstance(app.screen, ProjectDetailScreen)
        assert "nested" not in _module_names(detail)
