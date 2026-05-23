from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, TextArea
from textual.containers import Container, Center


class RepostDialog(ModalScreen):
    CSS_PATH = '../css/repost.tcss'

    def compose(self) -> ComposeResult:
        with Container(id='dialog'):
            yield TextArea(placeholder='Комментарий')
            with Container(id="button"):
                yield Button('Репостнуть', 'success')

    def on_mount(self):
        self.query_one('#dialog', Container).border_title = 'Репост'

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss(self.query_one(TextArea).text)