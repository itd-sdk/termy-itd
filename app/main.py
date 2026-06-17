from itd import ITDClient, ITDConfig, Notifications
from itd.exceptions import SessionExpiredError, SessionNotFoundError, SessionRevokedError
from itd.notification import Notification
from rich.console import RenderableType
from textual.app import App, ReturnType

from app.screens import HomeScreen, LoginScreen, NotificationsScreen
from app.storage import storage
from app.widgets.shared import ClickableStatic


class TermyITDApp(App):
    CSS_PATH = ['css/style.tcss', 'css/post.tcss', 'css/comment.tcss', 'css/notification.tcss']  # https://github.com/Textualize/textual/discussions/4509
    SCREENS = {'home': HomeScreen, 'notifications': NotificationsScreen}
    client: ITDClient

    def update_notifications_count(self, count: int | None = None):
        count = count or self.notifications.unread_count
        if count == 0:
            title = '  Уведомления'
        else:
            title = f' Уведомления [white on red]{count}[/]'

        for child in self.children:
            child.query_one('.notifications-tab', ClickableStatic).update(title)

    def _on_notification(self, notification: Notification):
        self.update_notifications_count(self.notifications.unread_count + 1)
        self.notify(
            notification.preview or notification.get_text(avatar=True),
            title=notification.get_text(avatar=True) if notification.preview else 'Новое уведомление',
            timeout=15
        )
        if self.is_screen_installed('notifications'):
            self.get_screen('notifications')._add_notification(notification)  # ty: ignore [unresolved-attribute]

    def on_mount(self):
        if storage.get('refresh'):
            self.client = ITDClient(
                storage['refresh'],
                config=ITDConfig('client', post_update_stats=False, post_view_increment=True, auto_load=False, load_on_iter=False, load_on_getitem=False)
            )
            try:
                self.client.refresh_auth()
                self.notifications = Notifications()
                self.notifications.on_notification = self._on_notification  # ty: ignore[invalid-assignment]
                self.notifications.stream_bg()
            except SessionExpiredError:
                self.notify('Сессия истекла', severity='error')
            except SessionNotFoundError:
                self.notify('Сессия не найдена', severity='error')
            except SessionRevokedError:
                self.notify('Сессия ревокнута (выход из аккаунта)', severity='error')
            else:
                self.push_screen('home')
                # self.update_notifications_count(self.notifications.unread_count)
                return
        self.push_screen(LoginScreen())

    def exit(self, result: ReturnType | None = None, return_code: int = 0, message: RenderableType | None = None):
        self.notifications.stop_stream()
        super().exit(result, return_code, message)


app = TermyITDApp()
app.run()
