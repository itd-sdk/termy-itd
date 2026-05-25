from asyncio import to_thread, sleep

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import LoadingIndicator, TabbedContent, TabPane
from textual.containers import VerticalScroll
from itd import Posts
from itd.enums import PostsTab, BATCH

from app.screens.base import BaseScreen
from app.widgets import PostWidget
from app.widgets.post import OriginalPostWidget

class HomeScreen(BaseScreen):
    CSS_PATH = '../css/home.tcss'
    BINDINGS = [
        Binding('j', 'next_post', 'Следующий пост'),
        Binding('k', 'prev_post', 'Предыдущий пост'),
        Binding('f5', 'refresh', 'Обновить страницу')
    ]

    def __init__(self) -> None:
        super().__init__()

        self.posts_map = {
            PostsTab.POPULAR: Posts(),
            PostsTab.FOLLOWING: Posts.following(),
            PostsTab.CLAN: Posts.clan()
        }
        self.tab = PostsTab.POPULAR
        self.focused_post: PostWidget | None = None

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
        for i, post in enumerate(self.posts.load(5)):
            # if i >= 20:
            #     break
            self.notify(f'load post {i}')
            result.append(post)
        return result

    @work(exclusive=True)
    async def load_posts(self):
        posts = self.query_one(f'#{self.tab.value}-posts', VerticalScroll)
        loading = LoadingIndicator()
        await posts.mount(loading)

        try:
            for post in await to_thread(self._fetch_posts):
                await posts.mount(PostWidget(post), before=loading)
        finally:
            await loading.remove()

    # def _outer_posts(self) -> list[PostWidget]:
    #     container = self.query_one(f'#{self.tab.value}-posts', VerticalScroll)
    #     return [w for w in container.children if isinstance(w, PostWidget)]

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

    async def action_refresh(self):
        posts = self.query_one(f'#{self.tab.value}-posts', VerticalScroll)
        await posts.remove_children()

        loading = LoadingIndicator()
        await posts.mount(loading)

        # self.posts.refresh(BATCH)
        self.focused_post = None
        self.posts.clear()
        for post in await to_thread(self._fetch_posts):
            await posts.mount(PostWidget(post), before=loading)
        await loading.remove()

        # analog to posts.scroll_home, original not updates scrollbar idk why
        posts.scroll_y = 0
        posts.scroll_target_y = 0
        if posts._vertical_scrollbar:
            posts._vertical_scrollbar.position = 0


    def on_mount(self):
        self.query_one(VerticalScroll).focus()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated):
        self.focused_post = None
        self.tab = PostsTab((event.tab.id or '').replace('--content-tab-', ''))
        if not self.posts:
            self.load_posts()

    @property
    def posts(self):
        return self.posts_map[self.tab]
