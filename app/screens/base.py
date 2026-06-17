from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Static
from textual_englyph import EnGlyphText

from app.dialogs import ConfirmDialog
from app.widgets.shared import ClickableStatic


class BaseScreen(Screen):
    DEFAULT_CSS = """
    EnGlyph {
        background: $panel;
    }
    """

    def __init__(self):
        super().__init__()
        self.current_tab: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id='sidebar'):
            with Vertical(id='logo'):
                yield EnGlyphText('termy', font_name='casio-fx-9860gii.ttf', font_size=6, basis=(2, 3))
                yield EnGlyphText('ИТД', font_name='casio-fx-9860gii.ttf', font_size=7, basis=(2, 3))

            for title, name in (
                ('󱀈  Главная', 'home'),
                ('  Уведомления', 'notifications'),
                ('  Поиск', 'search'),
                ('󱠽  Ивент', 'event'),
                ('  Профиль', 'profile')
            ):
                yield ClickableStatic(title, classes=f'{"active-tab" if self.current_tab == name else ""} tab {name}-tab')
            yield Static('termy-ITD by @fdg', id='about')
        yield Footer()

    def on_clickable_static_clicked(self, event: ClickableStatic.Clicked):
        event.stop()
        for _ in range(len(self.app.get_screen_stack()) - 1):
            self.app.pop_screen()
        self.log(event.classes)
        if 'home' in event.classes:
            self.app.push_screen('home')
        elif 'notifications' in event.classes:
            self.app.push_screen('notifications')
        else:
            self.app.push_screen('home')
            self.app.push_screen(ConfirmDialog('Ошибка', 'Не удалось найти экран'))

    @work
    async def set_notifications(self):
        self.app.update_notifications_count(self.app.notifications.unread_count)  # ty: ignore[unresolved-attribute]

    def on_mount(self):
        self.call_after_refresh(self.set_notifications)
