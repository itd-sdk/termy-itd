from itd import ITDClient
from itd.exceptions import SessionExpiredError, SessionNotFoundError, SessionRevokedError
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static
from textual_englyph import EnGlyphText

from app.screens.home import HomeScreen
from app.storage import flush, storage


class LoginScreen(Screen):
    CSS_PATH = '../css/login.tcss'
    DEFAULT_CSS = """
    EnGlyph {
        background: $panel; # idk why but it not works in a css file
    }
    """

    def compose(self):
        with Vertical(id='container'):
            with Center():
                yield EnGlyphText('ИТД', font_name='casio-fx-9860gii.ttf', font_size=8, basis=(1, 2))
            with Center():
                yield Input(placeholder='refresh_token')
            yield Static(id='error')
            with Center():
                yield Button('Войти', disabled=True, variant='primary')

    def on_input_changed(self, event: Input.Changed):
        self.query_one(Button).disabled = not bool(event.input.value)

    def on_button_pressed(self, event: Button.Pressed):
        input = self.query_one(Input)
        client = ITDClient(input.value)
        try:
            client.refresh_auth()
        except SessionNotFoundError:
            self.query_one('#error', Static).content = 'Сессия не найдена'
        except SessionExpiredError:
            self.query_one('#error', Static).content = 'Сессия истекла'
        except SessionRevokedError:
            self.query_one('#error', Static).content = 'Сессия ревокнута (выход из аккаунта)'
        else:
            storage['refresh'] = input.value
            flush()
            self.app.client = client  # ty: ignore[unresolved-attribute]
            self.app.switch_screen(HomeScreen())
