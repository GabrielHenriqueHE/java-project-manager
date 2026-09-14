import shutil
from pathlib import Path

import pytest
from textual.app import App
from textual.widgets import Tree

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


async def test_remove_module_without_dependents(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        detail = app.screen
        assert isinstance(detail, ProjectDetailScreen)
        tree = detail.query_one("#project-tree", Tree)
        tree.focus()

        # root -> bom -> core -> api
        await pilot.press("down", "down", "down", "enter")
        await pilot.pause()
        assert detail._selected_module.name == "api"

        await pilot.press("r")
        await pilot.pause()

        assert isinstance(app.screen, ProjectDetailScreen)
        assert "api" not in _module_names(detail)


async def test_remove_module_with_dependents_shows_confirm_and_removes(
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
        tree = detail.query_one("#project-tree", Tree)
        tree.focus()

        # root -> bom -> core
        await pilot.press("down", "down", "enter")
        await pilot.pause()
        assert detail._selected_module.name == "core"

        await pilot.press("r")
        await pilot.pause()
        assert type(app.screen).__name__ == "ConfirmModal"

        await pilot.click("#confirm-yes")
        await pilot.pause()

        assert isinstance(app.screen, ProjectDetailScreen)
        assert "core" not in _module_names(detail)
        assert not (project_root / "pom.xml").read_text().count("<module>core</module>")


async def test_remove_module_with_dependents_cancelled_keeps_module(
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
        tree = detail.query_one("#project-tree", Tree)
        tree.focus()

        await pilot.press("down", "down", "enter")
        await pilot.pause()
        assert detail._selected_module.name == "core"

        await pilot.press("r")
        await pilot.pause()
        await pilot.click("#confirm-no")
        await pilot.pause()

        assert isinstance(app.screen, ProjectDetailScreen)
        assert "core" in _module_names(detail)
