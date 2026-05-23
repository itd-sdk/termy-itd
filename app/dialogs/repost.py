from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, TextArea
from textual.containers import Horizontal, Container


class RepostDialog(ModalScreen):
    CSS_PATH = '../css/repost.tcss'
    BINDINGS = [Binding('escape', 'app.pop_screen', 'Отмена')]

    def compose(self) -> ComposeResult:
        with Container(id='dialog'):
            yield TextArea(placeholder='Комментарий')
            with Horizontal(id="dialog-buttons"):
                yield Button('Отмена')
                yield Button('Репостнуть', 'success')

    def on_mount(self):
        self.query_one('#dialog', Container).border_title = 'Репост'

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.variant == 'success':
            self.dismiss(self.query_one(TextArea).text)
        else:
            self.app.pop_screen()