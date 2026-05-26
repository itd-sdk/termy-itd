from textual.app import App
from itd import ITDClient, ITDConfig

from app.screens import LoginScreen, HomeScreen
from app.storage import storage


class TermyITDApp(App):
    CSS_PATH = ['css/style.tcss', 'css/post.tcss'] # https://github.com/Textualize/textual/discussions/4509
    client: ITDClient

    def on_mount(self):
        if storage.get('refresh'):
            self.client = ITDClient(storage['refresh'], config=ITDConfig(
                timeout=15,
                timeout_file=15,
                retry_enabled=False,
                dwell_enabled=True,
                post_update_stats=False,
                post_view_increment=True,
                auto_load=False,
                load_on_iter=False
            ))
            self.push_screen(HomeScreen())
        else:
            self.push_screen(LoginScreen())

app = TermyITDApp()
app.run()