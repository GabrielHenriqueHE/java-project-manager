from textual.app import App

from manager.screens.main_screen import MainScreen


class ManagerApp(App):
    """TUI para gerenciar projetos Java independente da build tool."""

    TITLE = "Java Project Manager"

    def on_mount(self) -> None:
        self.push_screen(MainScreen())


def main() -> None:
    ManagerApp().run()


if __name__ == "__main__":
    main()
