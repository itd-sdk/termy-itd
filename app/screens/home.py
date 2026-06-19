from itd import Posts
from textual.app import ComposeResult
from textual.widgets import TabbedContent, TabPane

from app.screens.base import BaseScreen
from app.widgets import PostsScroll, PostsWidget


class HomeScreen(BaseScreen):
    screen_name = 'home'

    def compose(self) -> ComposeResult:
        yield from super().compose()
        with TabbedContent():
            with TabPane('Популярное', id='popular'):
                with PostsScroll():
                    yield PostsWidget(Posts())

            with TabPane('Подписки', id='following'):
                with PostsScroll():
                    yield PostsWidget(Posts.following())

            with TabPane('Клан', id='clan'):
                with PostsScroll():
                    yield PostsWidget(Posts.clan())

    def on_mount(self):
        self.query_one(PostsWidget).focus()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated):
        self.focused_post = None
        posts = next((posts for posts in self.query(PostsWidget) if posts.tab == (event.tab.id or '').replace('--content-tab-', '')))
        if not posts.posts:
            posts.load_posts()
