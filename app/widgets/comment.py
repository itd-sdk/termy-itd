from webbrowser import open

from itd.comment import Comment
from pyperclip import copy
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from app.widgets.shared import CarouselDialog, ClickableStatic, ImageCarousel


class CommentWidget(Widget):
    class Replied(Message):
        def __init__(self, comment: Comment):
            super().__init__()
            self.comment = comment

    can_focus = True
    BINDINGS = [
        Binding('a', 'open_attachments', 'Открыть вложения'),
        Binding('l', 'like', 'Лайк'),
        Binding('ctrl+c', 'copy', 'Скопировать текст'),
        Binding('u', 'copy_url', 'Скопировать ссылку на комментарий'),
        Binding('U', 'open_url', 'Открыть комментарий в браузере'),
        Binding('delete', 'delete', 'Удалить комментарий'),
        Binding('alt+r', 'report', 'Пожаловаться')
    ]

    def __init__(self, comment: Comment) -> None:
        super().__init__()
        self.comment = comment

    def compose(self) -> ComposeResult:
        with Horizontal(classes='comment-top'):
            yield Static(self.comment.author.avatar, classes='avatar')
            with Vertical():
                with Horizontal(classes='display-name'):
                    yield Static(self.comment.author.display_name, classes='subscribed' if self.comment.author.is_subscribed else '', markup=False)
                    if self.comment.author.verified:
                        yield Static('', classes='verified')
                yield Static(f'@{self.comment.author.username}', classes='username')
            yield Static(self.comment.created_at.strftime('%d.%m.%y %H:%M:%S'), classes='date')
            with Horizontal(classes='actions'):
                yield ClickableStatic('󰒗', classes='share')
                yield ClickableStatic('', classes='copy')
                yield ClickableStatic('', classes='report')
                yield ClickableStatic('󰆴', classes='delete')

        yield Static(self.comment.content)

        if self.comment.attachments:
            yield ImageCarousel(self.comment.attachments)

        with Horizontal(classes='comment-bottom'):
            yield ClickableStatic('Ответить', classes='reply-button')
            yield ClickableStatic(
                f'{"" if self.comment.is_liked else ""} {self.comment.likes_count}', classes=f'likes{" active" if self.comment.is_liked else ""}'
            )

        if self.comment.replies.load_all():
            with Vertical(classes='replies'):
                for reply in self.comment.replies:
                    yield CommentWidget(reply)

    def action_like(self):
        button = self.query_one('.likes', ClickableStatic)

        if self.comment.is_liked:
            button.remove_class('active')
            self.comment.unlike()
            button.update(f' {self.comment.likes_count}')
        else:
            button.add_class('active')
            self.comment.like()
            button.update(f' {self.comment.likes_count}')

    def on_clickable_static_clicked(self, event: ClickableStatic.Clicked):
        event.stop()
        if 'likes' in event.classes:
            self.action_like()
        if 'reply' in event.classes:
            self.post_message(self.Replied(self.comment))

    def action_open_attachments(self):
        if self.comment.attachments:
            self.app.push_screen(CarouselDialog(self.comment.attachments))
        else:
            self.notify('Нет вложений', severity='warning')

    def action_copy(self):
        if self.comment.content:
            copy(self.comment.content)
            self.notify('Текст комментария скопирован')
        else:
            self.notify('Нечего копировать', severity='warning')

    def action_copy_url(self):
        copy(self.comment.url)
        self.notify('Ссылка на комментарий скопирована')

    def action_open_url(self):
        open(self.comment.url)
        self.notify('Комментарий должен открыться в браузере')
