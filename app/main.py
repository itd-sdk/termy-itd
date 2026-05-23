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
            self.push_screen(HomeScreen())
        else:
            self.push_screen(LoginScreen())

app = TermyITDApp()
app.run()