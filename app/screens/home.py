from asyncio import to_thread

from textual import work
from textual.app import ComposeResult
from textual.widgets import LoadingIndicator, TabbedContent, TabPane
from textual.containers import VerticalScroll
from itd import Posts
from itd.enums import PostsTab

from app.screens.base import BaseScreen
from app.widgets import PostWidget

class HomeScreen(BaseScreen):
    CSS_PATH = '../css/home.tcss'

    def __init__(self) -> None:
        super().__init__()

        self.posts_map = {
            PostsTab.POPULAR: Posts(),
            PostsTab.FOLLOWING: Posts.following(),
            PostsTab.CLAN: Posts.clan()
        }
        self.tab = PostsTab.POPULAR

    def compose(self) -> ComposeResult:
        for widget in super().compose():
            yield widget

        with TabbedContent():
            with TabPane('Популярное', id='popular'):
                yield VerticalScroll(id='popular-posts', classes='posts')

            with TabPane('Подписки', id='following'):
                yield VerticalScroll(id='following-posts', classes='posts')

            with TabPane('Клан', id='clan'):
                yield VerticalScroll(id='clan-posts', classes='posts')

    def _fetch_posts(self):
        result = []
        for i, post in enumerate(self.posts[:20]):
            # if i >= 20:
            #     break
            result.append(post)
        return result

    @work(exclusive=True)
    async def load_posts(self):
        posts = self.query_one(f'#{self.tab.value}-posts', VerticalScroll)
        loading = LoadingIndicator()
        await posts.mount(loading)

        try:
            fetched = await to_thread(self._fetch_posts)
            for post in fetched:
                await posts.mount(PostWidget(post), before=loading)
        finally:
            await loading.remove()

    def on_mount(self):
        self.query_one(VerticalScroll).focus()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated):
        self.tab = PostsTab((event.tab.id or '').replace('--content-tab-', ''))
        if not self.posts:
            self.load_posts()

    @property
    def posts(self):
        return self.posts_map[self.tab]
