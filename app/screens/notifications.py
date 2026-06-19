from itd.notification import Notification
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, LoadingIndicator, Static

from app.screens.base import BaseScreen
from app.widgets import NotificationWidget


class NotificationsScreen(BaseScreen):
    screen_name = 'notifications'
    BINDINGS = [Binding('R', 'read_all', 'Прочитать все уведы')]

    def compose(self) -> ComposeResult:
        yield from super().compose()
        with Horizontal():
            yield Static('Уведомления', classes='h1')
            yield Button('Прочитать все', variant='primary', id='read-all', flat=True, disabled=self.app.notifications.unread_count == 0)  # ty: ignore[unresolved-attribute]
        yield VerticalScroll()

    @work
    async def load_notifications(self):
        scroll = self.query_one(VerticalScroll)
        loading = LoadingIndicator()
        await scroll.mount(loading)

        try:
            for notification in self.app.notifications.load(20):  # ty: ignore[unresolved-attribute]
                await scroll.mount(NotificationWidget(notification), before=loading)
        finally:
            await loading.remove()

    def on_mount(self):
        self.load_notifications()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == 'read-all':
            self.action_read_all()
        event.stop()

    def action_read_all(self):
        if self.app.notifications.unread_count == 0:  # ty: ignore[unresolved-attribute]
            self.notify('Нет уведомлений', severity='warning')
            return
        self.app.notifications.read_all()  # ty: ignore[unresolved-attribute]
        for notification in self.query(NotificationWidget):
            if notification.has_class('unread'):
                notification._read()
        self.query_one('#read-all', Button).disabled = True
        self.app.update_notifications_count()  # ty: ignore[unresolved-attribute]

    def _add_notification(self, notification: Notification):
        self.app.call_from_thread(self.query_one(VerticalScroll).mount, NotificationWidget(notification), before=0)
