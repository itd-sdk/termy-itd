from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import Horizontal, Container
from textual.widgets import Button, Static


class ConfirmDialog(ModalScreen):
    BINDINGS = [
        Binding('escape', 'dismiss', 'Отмена'),
        Binding('ctrl+enter', 'dismiss(True)', 'ОК')
    ]

    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        self.title = title
        self.description = description

    def compose(self) -> ComposeResult:
        with Container(id='dialog'):
            yield Static(self.description)
            with Horizontal(id="dialog-buttons"):
                yield Button('Отмена', 'error')
                yield Button('ОК', 'success', id='ok')

    def on_mount(self):
        self.query_one('#dialog').border_title = self.title

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == 'ok':
            self.dismiss(True)
        else:
            self.dismiss(False)