from asyncio import to_thread

from itd import Post
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import LoadingIndicator, Static

from app.screens.base import BaseScreen
from app.widgets import CommentWidget, PostWidget


class PostScreen(BaseScreen):
    BINDINGS = [Binding('f5', 'refresh', 'Обновить страницу'), Binding('escape', 'app.pop_screen', 'Назад')]
    # CSS_PATH = '../css/post.tcss'

    def __init__(self, post: Post) -> None:
        super().__init__()
        self.post = post

    def compose(self) -> ComposeResult:
        yield from super().compose()

        yield Static('[@click=app.pop_screen][/] Пост', id='heading')
        with VerticalScroll():
            yield PostWidget(self.post)

    def _fetch_comments(self):
        return self.post.comments.load(100)

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
        self.load_comments()
