from itd import Post
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Static

from app.screens.base import BaseScreen
from app.widgets import PostWidget


class PostScreen(BaseScreen):
    BINDINGS = [
        Binding("f5", "refresh", "Обновить страницу"),
        Binding("alt+left", "app.pop_screen", "Назад")
    ]
    # CSS_PATH = '../css/post.tcss'

    def __init__(self, post: Post) -> None:
        super().__init__()
        self.post = post
        self.notify(str(post.id))

    def compose(self) -> ComposeResult:
        yield from super().compose()

        yield Static("[@click=app.pop_screen][/] Пост", id="heading")
        yield PostWidget(self.post)
