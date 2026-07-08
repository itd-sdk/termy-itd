from webbrowser import open

from itd.comment import Comment
from pyperclip import copy
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from app.widgets.shared import Avatar, CarouselDialog, ClickableStatic, DisplayName, ImageCarousel


class CommentWidget(Widget):
    class Replied(Message):
        def __init__(self, comment: Comment):
            super().__init__()
            self.comment = comment

    can_focus = True
    BINDINGS = [
        Binding('a', 'open_attachments', 'Вложения'),
        Binding('l', 'like', 'Лайк'),
        Binding('ctrl+c', 'copy', 'Скопировать текст'),
        Binding('u', 'copy_url', 'Скопировать ссылку'),
        Binding('U', 'open_url', 'Открыть в браузере'),
        Binding('delete', 'delete', 'Удалить'),
        Binding('alt+r', 'report', 'Пожаловаться')
    ]

    def __init__(self, comment: Comment, _base_comment: CommentWidget | None = None) -> None:
        super().__init__()
        self.comment = comment
        self._base_comment = _base_comment

    def compose(self) -> ComposeResult:
        with Horizontal(classes='comment-top'):
            yield Avatar(self.comment.author)
            with Vertical():
                yield DisplayName(self.comment.author)
                yield Static(f'@{self.comment.author.username}', classes='username')
            yield Static(self.comment.created_at.strftime('%d.%m.%y %H:%M:%S'), classes='date')

            with Horizontal(classes='actions'):
                yield ClickableStatic('󰒗', classes='share')
                yield ClickableStatic('', classes='copy')
                if self.comment.can_edit:
                    yield ClickableStatic('󰏫', classes='edit')
                if self.comment.can_report:
                    yield ClickableStatic('', classes='report')
                if self.comment.can_delete:
                    yield ClickableStatic('󰆴', classes='delete')

        yield Static(f'{f"[dim underline]@{self.comment.reply_to.username}[/] " if self.comment.reply_to is not None else ""}{self.comment.content}')

        if self.comment.attachments:
            yield ImageCarousel(self.comment.attachments)

        with Horizontal(classes='comment-bottom'):
            yield ClickableStatic('Ответить', classes='reply-button')
            yield ClickableStatic(
                f'{"" if self.comment.is_liked else ""} {self.comment.likes_count}', classes=f'likes{" active" if self.comment.is_liked else ""}'
            )

        if not self.comment.is_reply and self.comment.replies_count > 0:
            with Vertical(classes='replies'):
                for reply in self.comment.first_replies:
                    yield CommentWidget(reply, self)
                if len(self.comment.first_replies) < self.comment.replies_count:
                    yield ClickableStatic(
                        f'Загрузить еще [b]{min(100, self.comment.replies_count - len(self.comment.first_replies))}[/b] ответов', classes='load-replies'
                    )

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
        if 'load-replies' in event.classes:
            self.query_one('.load-replies', ClickableStatic).update('чел я это еще не добавил и тд')
            self.notify('todo', severity='error')

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

    def _mount_reply(self, reply: CommentWidget):
        assert self._base_comment
        self._base_comment.mount(reply, after=self)
