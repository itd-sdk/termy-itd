from textual.app import App
from itd import ITDClient

from app.screens import LoginScreen, HomeScreen
from app.storage import storage


class TermyITDApp(App):
    CSS_PATH = ['css/style.tcss', 'css/post.tcss'] # https://github.com/Textualize/textual/discussions/4509
    client: ITDClient

    def on_mount(self):
        if storage.get('refresh'):
            self.client = ITDClient(storage['refresh'])
            self.client.config.timeout = 10
            self.client.config.timeout_file = 10
            self.client.config.retry_enabled = False
            self.client.config.dwell_enabled = False
            self.client.config.post_update_stats = False
            self.client.config.auto_load = False
            self.push_screen(HomeScreen())
        else:
            self.push_screen(LoginScreen())

app = TermyITDApp()
app.run()