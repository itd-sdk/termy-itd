from textual.app import App
from itd import ITDClient

from app.screens import LoginScreen, HomeScreen
from app.storage import storage


class TermyITDApp(App):
    SCREENS = {
        'login': LoginScreen,
        'home': HomeScreen
    }
    CSS_PATH = 'css/style.tcss'
    client: ITDClient

    def on_mount(self):
        if storage.get('refresh'):
            self.client = ITDClient(storage['refresh'])
            self.push_screen('home')
        else:
            self.push_screen('login')

app = TermyITDApp()
app.run()