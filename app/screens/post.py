from asyncio import to_thread

from itd import Post
from itd.comment import Comment
from itd.exceptions import BannedWordError, NotFoundError
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Input, LoadingIndicator, Static

from app.screens.base import BaseScreen
from app.widgets import CommentWidget, PostWidget
from app.widgets.shared import ClickableStatic


class PostScreen(BaseScreen):
    BINDINGS = [
        Binding('f5', 'refresh', 'Обновить страницу'),
        Binding('escape', 'app.pop_screen', 'Назад'),
        Binding('c', 'focus_comment', 'Сфокусироваться на вводе комментария'),
        Binding('x', 'cancel_reply', 'Отменить ответ')
    ]
    # CSS_PATH = '../css/post.tcss'

    def __init__(self, post: Post) -> None:
        super().__init__()
        self.post = post
        self.replying_comment: Comment | None = None

    def compose(self) -> ComposeResult:
        yield from super().compose()

        yield Static('[@click=app.pop_screen][/] Пост', id='heading')
        with VerticalScroll():
            yield PostWidget(self.post)
        with Horizontal():
            yield Input(placeholder='Комментарий..', id='comment-input', max_length=1000)
            yield Button('Отправить', variant='primary', disabled=True, id='add-comment')

    def on_input_changed(self, event: Input.Changed):
        self.query_one(Button).disabled = not bool(event.input.value)

    def on_button_pressed(self):
        self.add_comment()

    def on_input_submitted(self):
        self.add_comment()

    def on_comment_widget_replied(self, event: CommentWidget.Replied):
        self.notify(event.comment.content)
        event.stop()
        if self.replying_comment is not None:
            self.action_cancel_reply()
        self.replying_comment = event.comment
        if self.replying_comment.content:
            if len(self.replying_comment.content) > 100:
                content = self.replying_comment.content[:100]
            else:
                content = self.replying_comment.content
        elif self.replying_comment.attachments:
            content = f'[i]Вложения ({len(self.replying_comment.attachments)}шт)[/i]'
        else:
            content = 'Пустой комментарий??'
        self.mount(
            Horizontal(
                Static(f'  {self.replying_comment.author.avatar} [bold underline]{self.replying_comment.author.display_name}[/]  {content}'),
                ClickableStatic('', classes='error'),
                id='reply-header'
            ),
            after='VerticalScroll'
        )
        self.query_one('#comment-input', Input).placeholder = 'Ответ..'

    def action_cancel_reply(self):
        self.replying_comment = None
        self.query_one('#reply-header').remove()
        self.query_one('#comment-input', Input).placeholder = 'Комментарий..'

    def on_clickable_static_clicked(self):
        self.action_cancel_reply()

    def action_focus_comment(self):
        self.query_one('#comment-input', Input).focus()

    @work
    async def _add_comment(self, value: str):
        self.post.add_comment(value)

    def add_comment(self):
        input = self.query_one(Input)
        scroll = self.query_one(VerticalScroll)
        try:
            self._add_comment(input.value)
        except NotFoundError:
            self.notify('Пост не найден', severity='error')
        except BannedWordError:
            self.notify('В комментарии содержутся запрещенные слова', severity='error')
        else:
            comment = CommentWidget(self.post.comments[0])
            scroll.mount(comment, before=1)
            scroll.scroll_to_widget(comment)
            comment.focus()
            input.clear()

    def _fetch_comments(self):
        if not self.post.comments:
            self.post.comments.load(20)
        return self.post.comments

    @work
    async def load_comments(self):
        loading = LoadingIndicator()
        scroll = self.query_one(VerticalScroll)
        await scroll.mount(loading)

        try:
            for comment in await to_thread(self._fetch_comments):
                await scroll.mount(CommentWidget(comment), before=loading)
        finally:
            await loading.remove()

    def on_mount(self):
        self.query_one(PostWidget).focus()
        self.load_comments()
