from textual.containers import Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Static
from textual_englyph import EnGlyphText

from app.dialogs import ConfirmDialog
from app.widgets.shared import ClickableStatic


class BaseScreen(Screen):
    screen_name: str = 'none'

    class Installed(Message):
        def __init__(self, screen: BaseScreen):
            super().__init__()
            self.screen = screen

    def __init__(self, _log: bool = True):
        super().__init__()
        if _log:
            self.log(f'open {self.screen_name} screen')

    def compose(self):
        with Vertical(id='sidebar'):
            with Vertical(id='logo'):
                yield EnGlyphText('termy', font_name='casio-fx-9860gii.ttf', font_size=6, basis=(2, 3))
                yield EnGlyphText('ИТД', font_name='casio-fx-9860gii.ttf', font_size=7, basis=(2, 3))  # шесть семь кстати

            for title, name in (
                ('󱀈  Главная', 'home'),
                (
                    '  Уведомления' if self.app.notifications.unread_count == 0 else f' Уведомления [white on red]{self.app.notifications.unread_count}[/]',  # ty: ignore
                    'notifications'
                ),
                ('  Поиск', 'search'),
                ('󱠽  Ивент', 'event'),
                ('  Профиль', 'profile')
            ):
                yield ClickableStatic(title, classes=f'{"active-tab" if self.screen_name == name else ""} tab {name}-tab')
                yield Static('', classes='tab-divider')
            yield Static('termy-itd by @fdg', id='about')
        yield Footer()

    def on_clickable_static_clicked(self, event: ClickableStatic.Clicked):
        event.stop()
        if 'home' in event.classes:
            self.app.switch_mode('home')
        elif 'notifications' in event.classes:
            self.app.switch_mode('notifications')
        elif 'search' in event.classes:
            self.app.switch_mode('search')
        elif 'profile' in event.classes:
            self.app.switch_mode('profile')
        else:
            self.log.error(f'unable to find screen classes={event.classes}')
            self.app.push_screen(ConfirmDialog('Ошибка', 'Не удалось найти экран'))

    def on_mount(self):
        self.post_message(self.Installed(self))
