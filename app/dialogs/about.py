from webbrowser import open

from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Static
from textual_englyph import EnGlyphText

from app import __version__
from app.widgets.shared import ClickableStatic


class AboutDialog(ModalScreen):
    BINDINGS = [Binding('escape', 'app.pop_screen', 'Закрыть')]

    def compose(self):
        with Container(id='dialog'):
            yield EnGlyphText('termy itd', font_name='casio-fx-9860gii.ttf', font_size=7, basis=(2, 3))
            yield Static(f'Версия [b]{__version__}[/b]')
            yield ClickableStatic('Автор проекта: [$primary]@fdg[/]', classes='author')
            yield ClickableStatic('Новости этого и других проектов: [$primary]@itd_sdk[/]', classes='news')
            yield ClickableStatic(' Открыть исходный код [$primary]󰏌[/]', classes='source')

    def on_clickable_static_clicked(self, event: ClickableStatic.Clicked):
        event.stop()
        if 'author' in event.classes:
            open('https://xn--d1ah4a.com/@fdg')
        if 'news' in event.classes:
            open('https://xn--d1ah4a.com/@itd_sdk')
        if 'source' in event.classes:
            open('https://github.com/itd-sdk/termy-itd')
