from webbrowser import open

from itd import Portal
from textual import work
from textual.containers import Center
from textual.reactive import reactive
from textual.widgets import Button, Static
from textual_nav import NavPage


class EventPage(NavPage, tab_name='Ивент', tab_icon='󱠽'):
    portal: reactive[Portal | None] = reactive(None, recompose=True)

    def compose(self):
        if self.portal and self.portal.active:
            with Center():
                yield Static(f'Ивент: [b]{self.portal.title}[/]')
            with Center():
                yield Button('Перейти', variant='primary')
            with Center():
                yield Static(self.portal.url, classes='dim')
        else:
            yield Static('Ивент не активен')

    def on_button_pressed(self):
        assert self.portal
        open(self.portal.url)
        self.notify('Ивент должен открыться в браузере')

    @work(exclusive=True, thread=True)
    def load_portal(self):
        self.log('event.load_portal')
        self.portal = Portal()

        def _():
            self.loading = False

        self.app.call_from_thread(_)

    def on_mount(self):
        self.log('event.on_mount')
        self.loading = True
        self.load_portal()
