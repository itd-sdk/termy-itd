from itd import ITDClient, ITDConfig, Notifications
from itd.exceptions import SessionExpiredError, SessionNotFoundError, SessionRevokedError
from itd.logger import setup_logging
from itd.notification import Notification
from textual import work
from textual.app import App
from textual.logging import TextualHandler

from app.screens import HomeScreen, LoginScreen, NotificationsScreen, SearchScreen, UserScreen
from app.screens.base import BaseScreen
from app.storage import storage
from app.widgets.shared import ClickableStatic

setup_logging('debug', colorful=True).addHandler(TextualHandler())


class TermyITDApp(App):
    CSS_PATH = ['css/style.tcss', 'css/post.tcss', 'css/comment.tcss', 'css/notification.tcss']  # https://github.com/Textualize/textual/discussions/4509
    MODES = {'home': HomeScreen, 'notifications': NotificationsScreen, 'profile': UserScreen, 'search': SearchScreen}
    client: ITDClient

    def __init__(self, ansi_color: bool = False):
        super().__init__(ansi_color=ansi_color)
        self.log('init')
        self.current_tab: str | None = None
        self.screens: set[BaseScreen] = set()

    def update_notifications_count(self, count: int | None = None):
        count = count or self.notifications.unread_count
        self.log(f'update notifications count count={count}')
        if count == 0:
            title = '  Уведомления'
        else:
            title = f' Уведомления [white on red]{count}[/]'

        for screen in self.screens:
            screen.query_one('.notifications-tab', ClickableStatic).update(title)

    def _on_notification(self, notification: Notification):
        self.update_notifications_count(self.notifications.unread_count)
        self.log(f'new notification type={notification.type.value}')
        self.notify(
            notification.preview or notification.get_text(avatar=True),
            title=notification.get_text(avatar=True) if notification.preview else 'Новое уведомление',
            timeout=15
        )
        if self.is_screen_installed('notifications'):
            self.get_screen('notifications')._add_notification(notification)  # ty: ignore [unresolved-attribute]

    def on_mount(self):
        if not storage.get('refresh'):
            self.push_screen(LoginScreen())

        try:
            self.client = ITDClient.from_file(
                'default',  #'termy-itd',
                initial_refresh=storage['refresh'],
                verify_refresh=True,
                config=ITDConfig(
                    'client', timeout=10, timeout_file=30, post_update_stats=False, post_view_increment=True, load_on_iter=None, load_on_getattr=False
                )
            )
        except SessionExpiredError:
            self.notify('Сессия истекла', severity='error')
        except SessionNotFoundError:
            self.notify('Сессия не найдена', severity='error')
        except SessionRevokedError:
            self.notify('Сессия ревокнута (выход из аккаунта)', severity='error')
        else:
            self.notifications = Notifications()
            self.notifications.on_notification = self._on_notification  # ty: ignore[invalid-assignment]
            self.switch_mode('home')
            self.call_after_refresh(self.load_notifications)
            return

        self.push_screen(LoginScreen())

    @work(thread=True, exclusive=True)
    def load_notifications(self):
        self.notifications.unread_count
        self.notifications.stream_bg(True)
        self.update_notifications_count()

    def on_base_screen_installed(self, event: BaseScreen.Installed):
        self.screens.add(event.screen)


app = TermyITDApp(ansi_color=False)
app.run()
