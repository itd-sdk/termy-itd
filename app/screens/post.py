from itd import Post
from itd.comment import Comment
from itd.enums import LoadStatus
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
        Binding('f5', 'refresh', 'Обновить'),
        Binding('escape', 'app.pop_screen', 'Назад'),
        Binding('c', 'focus_input', 'Сфокусироваться на поле ввода')
    ]
    # CSS_PATH = '../css/post.tcss'

    def __init__(self, post: Post) -> None:
        super().__init__(_log=False)
        self.current_tab = 'post'
        self.post = post
        self.replying_comment: Comment | None = None
        self.log(f'open post id={self.post.id}')

    def compose(self) -> ComposeResult:
        yield from super().compose()

        if self.post.load_status == LoadStatus.NO:
            yield LoadingIndicator()  # я займу все место и тд
            return

        yield Static('[@click=app.pop_screen][/] Пост', id='heading')
        with VerticalScroll():
            yield PostWidget(self.post)
        with Horizontal():
            yield Input(placeholder='Комментарий..', id='comment-input', max_length=1000)
            yield Button('Отправить', variant='primary', disabled=True, id='add-comment')

    def on_input_changed(self, event: Input.Changed):
        self.query_one(Button).disabled = not bool(event.input.value)

    async def on_button_pressed(self):
        self.add_comment()

    async def on_input_submitted(self):
        self.add_comment()

    async def on_comment_widget_replied(self, event: CommentWidget.Replied):
        event.stop()
        if self.replying_comment is not None:
            await self.action_cancel_reply()

        self.replying_comment = event.comment
        if self.replying_comment.content:
            if len(self.replying_comment.content) > 100:
                content = self.replying_comment.content[:100].split('\n')[0]
            else:
                content = self.replying_comment.content
        elif self.replying_comment.attachments:
            content = f'[i]Вложения ({len(self.replying_comment.attachments)}шт)[/i]'
        else:
            content = 'Пустой комментарий??'
        await self.mount(
            Horizontal(
                Static(f'  {self.replying_comment.author.avatar} [bold underline]{self.replying_comment.author.display_name}[/]  {content}'),
                ClickableStatic('', classes='error'),
                id='reply-header'
            ),
            after='VerticalScroll'
        )
        self.query_one('#comment-input', Input).placeholder = 'Ответ..'
        self.action_focus_input()

    def action_cancel_reply(self):
        self.replying_comment = None
        self.query_one('#reply-header').remove()
        self.query_one('#comment-input', Input).placeholder = 'Комментарий..'

    def on_clickable_static_clicked(self, event: ClickableStatic.Clicked):
        event.stop()
        if 'error' in event.classes:
            self.action_cancel_reply()

    def action_focus_input(self):
        self.query_one('#comment-input', Input).focus()

    @work(thread=True, exclusive=True)
    def add_comment(self):
        button = self.query_one('#add-comment', Button)
        input = self.query_one('#comment-input', Input)
        scroll = self.query_one(VerticalScroll)
        self.app.call_from_thread(button.set_loading, True)

        try:
            if self.replying_comment is not None:
                comment = CommentWidget(self.replying_comment.reply(input.value))
            else:
                comment = CommentWidget(self.post.add_comment(input.value))
        except NotFoundError:
            self.notify('Пост не найден', severity='error')
        except BannedWordError:
            self.notify('В комментарии содержутся запрещенные слова', severity='error')
        else:
            if self.replying_comment is None:
                self.app.call_from_thread(scroll.mount, comment, before=1)

            else:
                for child in scroll.query(CommentWidget):
                    if child.comment.id == self.replying_comment.id:
                        if not child.comment.is_reply:
                            self.app.call_from_thread(child.query_one('.replies').mount, comment, before=1)
                        else:
                            self.app.call_from_thread(child._mount_reply, comment)
                        break

            scroll.scroll_to_widget(comment)
            comment.focus()
            input.clear()
            if self.replying_comment is not None:
                self.action_cancel_reply()
            self.app.call_from_thread(button.set_loading, False)

    @work(thread=True, exclusive=True)
    def load_comments(self):
        if self.post.comments_count == 0:
            return
        self.log('load comments')
        loading = LoadingIndicator()
        scroll = self.query_one(VerticalScroll)
        self.app.call_from_thread(scroll.mount, loading, after=1)

        if not self.post.comments:
            self.post.comments.load(50)
        for comment in self.post.comments:
            self.app.call_from_thread(scroll.mount, CommentWidget(comment), before=loading)

        loading.remove()

    @work(thread=True, exclusive=True)
    def load_post(self):
        self.log('load post')
        try:
            self.post.refresh()
        except NotFoundError:
            self.notify('Пост не найден', severity='error')
            self.app.pop_screen()
        else:
            self.refresh(recompose=True)
            self.call_after_refresh(self.load_comments)

    def on_mount(self):
        if self.post.load_status != LoadStatus.FULL:
            self.load_post()
        else:
            self.query_one(PostWidget).focus()
            self.load_comments()
