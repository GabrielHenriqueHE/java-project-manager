from pathlib import Path

import pytest
from textual.app import App
from textual.widgets import DataTable, Input, Tree

from manager.screens.dashboard import DashboardScreen
from manager.screens.project_detail import ProjectDetailScreen
from manager.services.registry import ProjectRegistry

FIXTURE = Path(__file__).parent / "fixtures" / "maven-multi-module"


class _TestApp(App):
    def __init__(self, registry: ProjectRegistry):
        super().__init__()
        self._project_registry = registry

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen(self._project_registry))


@pytest.fixture
def registry(tmp_path) -> ProjectRegistry:
    return ProjectRegistry(tmp_path / "registry.json")


async def test_dashboard_renders_empty_table(registry):
    app = _TestApp(registry)
    async with app.run_test() as pilot:
        await pilot.pause()
        table = app.screen.query_one("#projects-table", DataTable)
        assert table.row_count == 0


async def test_import_flow_registers_project_and_updates_dashboard(registry):
    app = _TestApp(registry)
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        await pilot.press("i")
        await pilot.pause()

        path_input = app.screen.query_one("#path-input", Input)
        path_input.value = str(FIXTURE)
        await pilot.press("enter")
        await pilot.pause(0.8)

        table = app.screen.query_one("#projects-table", DataTable)
        assert table.row_count == 1
        assert len(registry.load()) == 1


async def test_open_project_shows_module_tree(registry):
    registry.add(FIXTURE, "maven")
    app = _TestApp(registry)
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(app.screen, ProjectDetailScreen)
        tree = app.screen.query_one("#project-tree", Tree)
        assert len(tree.root.children) == 3


async def test_remove_project_clears_dashboard(registry):
    registry.add(FIXTURE, "maven")
    app = _TestApp(registry)
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()

        table = app.screen.query_one("#projects-table", DataTable)
        assert table.row_count == 0
        assert registry.load() == []
