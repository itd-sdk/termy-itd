from asyncio import to_thread

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Static
from itd import Post

from app.screens.base import BaseScreen
from app.widgets import PostWidget


class PostScreen(BaseScreen):
    BINDINGS = [
        Binding('f5', 'refresh', 'Обновить страницу')
    ]
    # CSS_PATH = '../css/post.tcss'

    def __init__(self, post: Post) -> None:
        super().__init__()
        self.post = post

    def compose(self) -> ComposeResult:
        yield from super().compose()

        yield Static('[@click=app.pop_screen][/] Пост', id='heading')
        yield PostWidget(self.post)
