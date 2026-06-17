from itd import Post
from itd.enums import NotificationTargetType
from itd.notification import Notification
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.widget import Widget
from textual.widgets import Static

from app.widgets.shared import Avatar, ClickableStatic, DisplayName


class NotificationWidget(Widget, can_focus=True):
    BINDINGS = [Binding('a', 'open_actor', 'Открыть профиль актора'), Binding('enter', 'open_target', 'Открыть объект'), Binding('r', 'read', 'Прочитать')]

    def __init__(self, notification: Notification):
        super().__init__()
        self.notification = notification
        if not notification.is_read:
            self.add_class('unread')

    def compose(self):
        yield Avatar(self.notification.actor.avatar, classes=self.notification.get_color())
        with Vertical():
            with Horizontal(classes='display-name'):
                yield DisplayName(self.notification.actor)
                yield Static(self.notification.get_text().replace(self.notification.actor.display_name, '').strip(), classes='notification-text')
                with Horizontal(classes='notification-actions'):
                    yield ClickableStatic('󰏋', classes='open-actor')
                    if self.notification.target_id is not None:
                        yield ClickableStatic('󰏌', classes='open-target')
                    if not self.notification.is_read:
                        yield ClickableStatic('󰄬', classes='read')

            if self.notification.preview:
                yield Static(self.notification.preview)

            yield Static(self.notification.created_at.strftime('%d.%m.%y %H:%M:%S'), classes='notification-date')

    def on_clickable_static_clicked(self, event: ClickableStatic.Clicked):
        event.stop()
        if 'open-target' in event.classes:
            self.action_open_target()
        if 'open-actor' in event.classes:
            self.action_open_actor()
        if 'read' in event.classes:
            self.action_read()

    def action_open_target(self):
        self.notify(str(self.notification.target_id))
        if self.notification.target_id and self.notification.target_type == NotificationTargetType.POST:
            from app.screens.post import PostScreen  # circular import

            self.app.push_screen(PostScreen(Post(self.notification.target_id)))
        else:
            self.notify(f'not implemented for {self.notification.target_type}', severity='error')

    def action_open_actor(self):
        self.notify(str(self.notification.actor.username))
        self.notify('todo', severity='error')

    def action_read(self):
        if self.notification.is_read:
            self.notify('Уведомление уже прочитано', severity='warning')
            return
        self.notification.read()
        self._read()
        self.app.update_notifications_count()  # ty: ignore[unresolved-attribute]

    def _read(self):
        self.notification.is_read = True
        self.remove_class('unread')
        self.query_one('.read').remove()

    def on_click(self, event: Click):
        if event.chain > 1:
            self.action_open_target()
