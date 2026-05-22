from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Vertical, Horizontal
from textual_englyph import EnGlyphText


class BaseScreen(Screen):
    DEFAULT_CSS = """
    EnGlyph {
        background: $panel;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id='sidebar'):
            with Vertical(id="logo"):
                yield EnGlyphText('termy', font_name='casio-fx-9860gii.ttf', font_size=6, basis=(2, 3))
                yield EnGlyphText('ИТД', font_name='casio-fx-9860gii.ttf', font_size=7, basis=(2, 3))

            yield Static('󱀈  Главная', classes='tab')
            yield Static('  Уведомления', classes='tab')
            yield Static('  Поиск', classes='tab')
            yield Static('󱠽  Ивент', classes='tab')
            yield Static('  Профиль', classes='tab')
            yield Static('termy-ITD by @fdg', id='about')