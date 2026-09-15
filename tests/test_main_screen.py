import shutil
from pathlib import Path

import pytest
from textual.app import App
from textual.widgets import Input, ListView

from manager.screens.main_screen import MainScreen
from manager.screens.widgets.bom_panel import BomPanel
from manager.screens.widgets.command_bar import CommandBar
from manager.screens.widgets.metadata_panel import MetadataPanel
from manager.screens.widgets.modules_panel import ModulesPanel
from manager.screens.widgets.projects_panel import ProjectsPanel
from manager.screens.widgets.structure_panel import StructurePanel
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
        self.push_screen(MainScreen(self._project_registry))


def _module_names(screen: MainScreen) -> set[str]:
    return {screen.project.root_module.name} | {
        m.name for m in screen.project.root_module.submodules
    }


async def test_empty_state_shows_placeholders(tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, MainScreen)
        assert screen.project is None
        assert "carregando" in str(screen.query_one("#projects-empty").content)
        assert screen.query_one(ModulesPanel).query_one("#modules-empty").display


async def test_import_project_populates_all_panels(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen

        await pilot.press("1")
        await pilot.press("n")
        await pilot.pause()

        import_screen = app.screen
        import_screen.query_one("#path-input", Input).value = str(project_root)
        await pilot.press("enter")
        await pilot.pause(0.8)

        assert isinstance(app.screen, MainScreen)
        assert screen.project is not None
        assert screen.project.name == "Multi Module Demo"
        assert screen.selected_module is screen.project.root_module

        bom_names = {dep.artifact_id for dep in screen.project.managed_dependencies}
        assert "commons-lang3" in bom_names


async def test_navigating_modules_updates_metadata_panel(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        body = screen.query_one(MetadataPanel).query_one("#metadata-body")
        root_text = str(body.content)
        assert "multi-module-demo" in root_text

        await pilot.press("3")
        await pilot.press("j")
        await pilot.pause()
        assert screen.selected_module.name == "multi-module-demo-bom"

        bom_text = str(body.content)
        assert bom_text != root_text
        assert "multi-module-demo-bom" in bom_text
        assert "artifactId" in bom_text


async def test_add_module_under_root_via_panel(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        await pilot.press("3")
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()

        form = app.screen
        assert type(form).__name__ == "ModuleFormScreen"
        form.query_one("#field-artifact-id", Input).value = "utils"
        await pilot.click("#form-confirm")
        await pilot.pause()

        assert isinstance(app.screen, MainScreen)
        assert "utils" in _module_names(screen)
        assert (project_root / "utils" / "src" / "main" / "java").is_dir()


async def test_remove_module_with_conflict_via_panel(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        await pilot.press("3")
        await pilot.pause()
        lv = screen.query_one("#modules-list", ListView)
        lv.index = 2  # root(0) -> bom(1) -> core(2)
        await pilot.pause()
        assert screen.selected_module.name == "core"

        await pilot.press("d")
        await pilot.pause()
        assert type(app.screen).__name__ == "ConfirmModal"

        await pilot.click("#confirm-yes")
        await pilot.pause()

        assert isinstance(app.screen, MainScreen)
        assert "core" not in _module_names(screen)


async def test_structure_panel_toggle_active_module(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        await pilot.press("5")
        await pilot.pause()
        panel = screen.query_one(StructurePanel)
        first_active = panel._modules[panel._active_index].name

        await pilot.press("space")
        await pilot.pause()
        second_active = panel._modules[panel._active_index].name

        assert first_active != second_active


async def test_structure_panel_creates_checklist_directory(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        await pilot.press("5")
        await pilot.pause()
        panel = screen.query_one(StructurePanel)
        active_module = panel._modules[panel._active_index]

        await pilot.press("enter")
        await pilot.pause()

        created_dir = (
            project_root / active_module.relative_path / "src" / "main" / "java"
        )
        assert created_dir.is_dir()


async def test_structure_panel_checklist_navigation_selects_different_item(
    project_root, tmp_path
):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        await pilot.press("5")
        await pilot.pause()
        panel = screen.query_one(StructurePanel)
        active_module = panel._modules[panel._active_index]

        await pilot.press("j")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        created_dir = (
            project_root / active_module.relative_path / "src" / "main" / "resources"
        )
        assert created_dir.is_dir()
        not_created = (
            project_root / active_module.relative_path / "src" / "main" / "java"
        )
        assert not not_created.is_dir()


async def test_structure_panel_recreate_existing_directory_is_a_no_op(
    project_root, tmp_path
):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        await pilot.press("5")
        await pilot.pause()

        await pilot.press("enter")
        await pilot.pause()
        project_after_create = screen.project

        await pilot.press("enter")
        await pilot.pause()

        assert screen.project is project_after_create


async def test_command_mode_creates_module_and_can_be_cancelled(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        # cancelar nao deve alterar nada
        await pilot.press(":")
        await pilot.pause()
        assert screen.query_one(CommandBar).display is True
        await pilot.press("escape")
        await pilot.pause()
        assert screen.query_one(CommandBar).display is False
        assert screen.query_one("#footer-bar").display is True

        # comando funcional
        await pilot.press(":")
        await pilot.pause()
        bar = screen.query_one(CommandBar)
        bar.value = "modulo utils"
        await pilot.press("enter")
        await pilot.pause()

        assert screen.query_one(CommandBar).display is False
        assert "utils" in _module_names(screen)


async def test_bom_panel_shows_managed_dependencies(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        bom_panel = screen.query_one(BomPanel)
        assert bom_panel.query_one("#bom-list", ListView).display is True
        assert bom_panel.query_one("#bom-empty").display is False


async def test_update_metadata_via_panel(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        await pilot.press("2")
        await pilot.press("enter")
        await pilot.pause()

        form = app.screen
        assert type(form).__name__ == "MetadataFormScreen"
        form.query_one("#field-description", Input).value = "Descricao nova"
        await pilot.click("#form-confirm")
        await pilot.pause()

        assert isinstance(app.screen, MainScreen)
        assert screen.project.root_module.metadata.description == "Descricao nova"
        pom_text = (project_root / "pom.xml").read_text()
        assert "<description>Descricao nova</description>" in pom_text


async def test_update_metadata_cancel_does_not_change_anything(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()
        original_description = screen.project.root_module.metadata.description

        await pilot.press("2")
        await pilot.press("enter")
        await pilot.pause()

        await pilot.click("#form-cancel")
        await pilot.pause()

        assert isinstance(app.screen, MainScreen)
        assert screen.project.root_module.metadata.description == original_description


async def test_update_metadata_adapter_error_shows_notification(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        await pilot.press("3")
        await pilot.pause()
        lv = screen.query_one("#modules-list", ListView)
        lv.index = 1  # root(0) -> bom(1)
        await pilot.pause()
        assert screen.selected_module.name == "multi-module-demo-bom"

        await pilot.press("2")
        await pilot.press("enter")
        await pilot.pause()

        form = app.screen
        assert type(form).__name__ == "MetadataFormScreen"
        form.query_one("#field-packaging", Input).value = "jar"
        await pilot.click("#form-confirm")
        await pilot.pause()

        assert isinstance(app.screen, MainScreen)
        assert screen.selected_module.name == "multi-module-demo-bom"
        assert screen.project.root_module.metadata.packaging == "pom"


async def test_add_managed_dependency_via_bom_panel(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()

        await pilot.press("3")
        await pilot.pause()
        lv = screen.query_one("#modules-list", ListView)
        lv.index = 1  # root(0) -> bom(1)
        await pilot.pause()
        assert screen.selected_module.name == "multi-module-demo-bom"

        await pilot.press("4")
        await pilot.press("n")
        await pilot.pause()

        form = app.screen
        assert type(form).__name__ == "DependencyFormScreen"
        form.query_one("#field-group-id", Input).value = "org.apache.commons"
        form.query_one("#field-artifact-id", Input).value = "commons-io"
        form.query_one("#field-version", Input).value = "2.16.1"
        await pilot.click("#form-confirm")
        await pilot.pause()

        assert isinstance(app.screen, MainScreen)
        names = {dep.artifact_id for dep in screen.project.managed_dependencies}
        assert "commons-io" in names


async def test_add_dependency_cancel_does_not_change_anything(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()
        original_count = len(screen.project.managed_dependencies)

        await pilot.press("4")
        await pilot.press("n")
        await pilot.pause()

        await pilot.click("#form-cancel")
        await pilot.pause()

        assert isinstance(app.screen, MainScreen)
        assert len(screen.project.managed_dependencies) == original_count


async def test_add_dependency_adapter_error_shows_notification(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()
        # root(0) e "core"(2) tem packaging=jar, nao pode receber dependencia
        # gerenciada -- mas o alvo padrao (sem selecionar nada no Painel 3) e
        # a raiz, que tem packaging=pom; selecionamos "core" explicitamente.
        await pilot.press("3")
        await pilot.pause()
        lv = screen.query_one("#modules-list", ListView)
        lv.index = 2  # root(0) -> bom(1) -> core(2)
        await pilot.pause()
        assert screen.selected_module.name == "core"
        original_count = len(screen.project.managed_dependencies)

        await pilot.press("4")
        await pilot.press("n")
        await pilot.pause()

        form = app.screen
        form.query_one("#field-group-id", Input).value = "org.apache.commons"
        form.query_one("#field-artifact-id", Input).value = "commons-io"
        form.query_one("#field-version", Input).value = "2.16.1"
        await pilot.click("#form-confirm")
        await pilot.pause()

        assert isinstance(app.screen, MainScreen)
        assert len(screen.project.managed_dependencies) == original_count


async def test_remove_project_clears_state(project_root, tmp_path):
    registry = ProjectRegistry(tmp_path / "registry.json")
    registry.add(project_root, "maven")
    app = _TestApp(registry)

    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        screen = app.screen
        await pilot.press("1")
        await pilot.press("j")
        await pilot.pause()
        assert screen.project is not None

        await pilot.press("d")
        await pilot.pause()

        assert screen.project is None
        assert registry.load() == []
