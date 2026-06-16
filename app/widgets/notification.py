from itd.notification import Notification
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static

from app.widgets.shared import ClickableStatic


class NotificationWidget(Widget, can_focus=True):
    BINDINGS = [
        Binding('enter', 'open_target', 'Открыть объект'),
        Binding('ctrl+enter', 'open_actor', 'Открыть профиль актора'),
        Binding('r', 'read', 'Прочитать')
    ]

    def __init__(self, notification: Notification):
        super().__init__()
        self.notification = notification
        self.add_class(notification.get_color())
        if not notification.is_read:
            self.add_class('unread')

    def compose(self):
        yield Static(self.notification.actor.avatar, classes='avatar')
        with Vertical():
            with Horizontal(classes='display-name'):
                yield Static(self.notification.actor.display_name, classes='subscribed' if self.notification.actor.is_subscribed else '', markup=False)
                if self.notification.actor.verified:
                    yield Static('', classes='verified')
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
        self.notify('todo', severity='error')

    def action_open_actor(self):
        self.notify(str(self.notification.actor.username))
        self.notify('todo', severity='error')

    def action_read(self):
        if self.notification.is_read:
            self.notify('Уведомление уже прочитано', severity='error')
            return
        self.notification.read()
        self._read()

    def _read(self):
        self.remove_class('unread')
        self.query_one('.read').remove()
