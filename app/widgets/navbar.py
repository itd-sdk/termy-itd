from textual.containers import Vertical
from textual_englyph import EnGlyphText
from textual_nav.widgets import NavigationDrawer

from app.dialogs.about import AboutDialog
from app.widgets.shared import ClickableStatic


class TermyNavigationDrawer(NavigationDrawer, layout='vertical'):
    def compose(self):
        with Vertical(id='logo'):
            yield EnGlyphText('termy', font_name='casio-fx-9860gii.ttf', font_size=6, basis=(2, 3))
            yield EnGlyphText('ИТД', font_name='casio-fx-9860gii.ttf', font_size=7, basis=(2, 3))  # шесть семь кстати
        yield from super().compose()

    def on_clickable_static_clicked(self, event: ClickableStatic.Clicked):
        self.app.push_screen(AboutDialog())
