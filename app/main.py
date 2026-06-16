from itd import ITDClient, ITDConfig
from itd.exceptions import SessionExpiredError, SessionNotFoundError, SessionRevokedError
from textual.app import App

from app.screens import HomeScreen, LoginScreen
from app.storage import storage


class TermyITDApp(App):
    CSS_PATH = ['css/style.tcss', 'css/post.tcss', 'css/comment.tcss']  # https://github.com/Textualize/textual/discussions/4509
    client: ITDClient

    def on_mount(self):
        if storage.get('refresh'):
            self.client = ITDClient(
                storage['refresh'],
                config=ITDConfig('client', post_update_stats=False, post_view_increment=True, auto_load=False, load_on_iter=False, load_on_getitem=False)
            )
            try:
                self.client.refresh_auth()
            except SessionExpiredError:
                self.notify('Сессия истекла', severity='error')
            except SessionNotFoundError:
                self.notify('Сессия не найдена', severity='error')
            except SessionRevokedError:
                self.notify('Сессия ревокнута (выход из аккаунта)', severity='error')
            else:
                self.push_screen(HomeScreen())
                return
        self.push_screen(LoginScreen())


app = TermyITDApp()
app.run()
