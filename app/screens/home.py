from asyncio import to_thread

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import LoadingIndicator, TabbedContent, TabPane
from textual.containers import VerticalScroll
from itd import Posts
from itd.enums import PostsTab

from app.screens.base import BaseScreen
from app.widgets import PostWidget
from app.widgets.post import OriginalPostWidget


class PostsWidget(VerticalScroll):
    BINDINGS = [
        Binding('j', 'next_post', 'Следующий пост'),
        Binding('k', 'prev_post', 'Предыдущий пост'),
        Binding('f5', 'refresh', 'Обновить страницу')
    ]

    def __init__(self, tab: PostsTab = PostsTab.POPULAR) -> None:
        super().__init__(classes='posts', id=f'{tab.value}-posts')
        self.posts = Posts(tab)
        self.tab = tab
        self.focused_post: PostWidget | None = None
        self.is_load_locked: bool = False


    def _fetch_posts(self):
        result = []
        for post in self.posts.load(20):
            result.append(post)
        return result

    @work(exclusive=True)
    async def load_posts(self):
        if self.is_load_locked:
            return
        self.is_load_locked = True
        if len(self.children) > 20:
            for child in self.children[:20]:
                await child.remove()

        loading = LoadingIndicator()
        await self.mount(loading)
        try:
            for post in await to_thread(self._fetch_posts):
                self.mount(PostWidget(post), before=loading)
        finally:
            await loading.remove()

        self.is_load_locked = False

    def action_next_post(self):
        posts = [post for post in self.query(PostWidget) if not isinstance(post, OriginalPostWidget)]
        if not posts:
            self.notify('Нет постов', severity='warning')
            return

        if not self.focused_post:
            posts[0].focus()
            self.focused_post = posts[0]
        else:
            post = posts[min(posts.index(self.focused_post) + 1, len(posts) - 1)]
            post.focus()
            self.focused_post = post

    def action_prev_post(self):
        posts = [post for post in self.query(PostWidget) if not isinstance(post, OriginalPostWidget)]
        if not posts:
            self.notify('Нет постов', severity='warning')
            return

        if not self.focused_post:
            posts[-1].focus()
            self.focused_post = posts[-1]
        else:
            post = posts[max(posts.index(self.focused_post) - 1, 0)]
            post.focus()
            self.focused_post = post

    def action_refresh(self):
        self.remove_children()

        self.focused_post = None
        self.posts.clear()
        self.load_posts()

        # analog to self.scroll_home, original not updates scrollbar idk why
        self.scroll_y = 0
        self.scroll_target_y = 0
        # if self._vertical_scrollbar:
        #     self._vertical_scrollbar.position = 0


    def watch_scroll_y(self, old_value: float, new_value: float) -> None:
        super().watch_scroll_y(old_value, new_value)
        if not self.is_load_locked and round(new_value) == self.max_scroll_y:
            self.load_posts()

    # def on_mount(self):
    #     self.load_posts()


class HomeScreen(BaseScreen):
    CSS_PATH = '../css/home.tcss'

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        for widget in super().compose():
            yield widget

        with TabbedContent():
            with TabPane('Популярное', id='popular'):
                yield PostsWidget()

            with TabPane('Подписки', id='following'):
                yield PostsWidget(PostsTab.FOLLOWING)

            with TabPane('Клан', id='clan'):
                yield PostsWidget(PostsTab.CLAN)

    def on_mount(self):
        self.query_one(PostsWidget).focus()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated):
        self.focused_post = None
        posts = next((posts for posts in self.query(PostsWidget) if posts.tab == PostsTab((event.tab.id or '').replace('--content-tab-', ''))))
        if not posts.posts:
            posts.load_posts()

