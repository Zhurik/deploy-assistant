from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import (
    Label,
    Static,
    Button,
)

from deploy_assistant.git import LocalRepo


class SelectedItemsScreen(ModalScreen):
    """Модалка для подтверждения деплоя."""

    CSS_PATH = "modal.tcss"

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    def __init__(self, repos: list[LocalRepo]):
        self.repos = repos
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.repos:
            items_content = "\n".join(
                [
                    f"- {repo.name}: {repo.version} -> {repo.new_version}"
                    for repo in self.repos
                ]
            )

            yield Vertical(
                Label("`Херачим?`", id="selected-items-title"),
                Static(items_content, id="selected-items-content"),
                Label(
                    f"Всего выбрано: {len(self.repos)}\nESC чтобы закрыть",
                    id="selected-items-footer",
                ),
                Vertical(
                    Button("Нет", id="no-button", variant="error"),
                    Button("Да", id="yes-button", variant="success"),
                    id="buttons-container",
                ),
                id="selected-items-dialog",
            )

        else:
            yield Vertical(
                Label("`А нахера?`", id="selected-items-title"),
                Label(
                    "Ничего не выбрано\nESC чтобы закрыть",
                    id="selected-items-footer",
                ),
                id="selected-items-dialog",
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "yes-button":
            self.deploy()
        elif event.button.id == "no-button":
            self.app.pop_screen()

    def deploy(self) -> None:
        """Create a JSON file with selected services info."""
        self.app.pop_screen()

        for repo in self.repos:
            try:
                repo.deploy()
                # Show success notification
                self.app.notify(
                    f"Запушил сервис {repo.name} с версией {repo.new_version}",
                    title="Успешный деплой",
                    severity="information",
                    timeout=5,
                )
            except Exception:
                # Show error notification
                self.app.notify(
                    f"Что-то пошло не так при деплое {repo.name}",
                    title="Ошибка деплоя",
                    severity="error",
                    timeout=10,
                )
