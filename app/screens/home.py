from asyncio import new_event_loop

from textual import work
from textual.app import ComposeResult
from textual.widgets import LoadingIndicator
from textual.containers import VerticalScroll
from itd import Posts

from app.screens.base import BaseScreen
from app.widgets import PostWidget

class HomeScreen(BaseScreen):
    def compose(self) -> ComposeResult:
        for widget in super().compose():
            yield widget

        yield VerticalScroll(id='posts')

    @work(exclusive=True)
    async def load_posts(self):
        posts = self.query_one('#posts', VerticalScroll)
        loading = LoadingIndicator()
        await posts.mount(loading)

        for i, post in enumerate(Posts()):
            if i > 20:
                break
            await posts.mount(PostWidget(post), before=loading)

        await loading.remove()

    def on_mount(self):
        self.load_posts()
