from itd import User
from itd.enums import LoadStatus
from textual import work
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import LoadingIndicator, Static
from textual_image.widget import SixelImage

from app.cache import get_and_maybe_write
from app.screens.base import BaseScreen
from app.widgets import PostsScroll, PostsWidget
from app.widgets.shared import Avatar, ClickableStatic, DisplayName


class Counter(ClickableStatic):
    def __init__(self, name: str, value: int):
        super().__init__(f'{value} [$foreground-muted]{name}[/]')
        self.counter_name = name
        self.counter_value = value


class UserScreen(BaseScreen):
    screen_name = 'user'
    CSS_PATH = '../css/user.tcss'
    BINDINGS = [Binding('escape', 'app.pop_screen', 'Назад')]

    def __init__(self, user: User | None = None):
        super().__init__(_log=False)
        self.user = user or User(self.app.client.user_id)  # ty: ignore
        self.log(f'open user screen username={user.username if user else "me"}')

    def compose(self):
        yield from super().compose()

        if self.user.load_status != LoadStatus.NO:
            yield LoadingIndicator()  # я займу все место и тд
            return

        with PostsScroll():
            yield SixelImage(on_error=lambda _: Static('Ошибка обработки банера', classes='attach-error'), classes='banner')

            with Vertical(classes='user-info'):
                with Horizontal():
                    yield Avatar(self.user, clickable=False, classes='blue' if self.user.is_subscribed else '')
                    with Vertical():
                        with Horizontal():
                            yield DisplayName(self.user, clickable=False)
                            yield Static(f'@{self.user.username}', classes='username')

                        if self.user.bio:
                            yield Static(self.user.bio, classes='bio')

                        if self.user.online:
                            yield Static('Онлайн', classes='online')
                        elif self.user.last_seen:
                            yield Static(f'Был {self.user.last_seen}', classes='last-seen')
                        else:
                            yield Static('Был хз когда', classes='last-seen')

                with Horizontal():
                    yield Counter('подписчиков', self.user.followers_count or 0)
                    yield Counter('подписок', self.user.following_count or 0)
                    yield Counter('постов', self.user.posts_count or 0)

            yield PostsWidget(self.user.posts)

    # @work(thread=True)
    # def load_user(self):
    #     self.user.refresh()
    #     self.query_one('.user-info').loading = False
    #     if self.user.banner:
    #         self.load_banner()
    #     self.refresh()

    @work(thread=True, exclusive=True)
    def load_banner(self):
        if not self.user.banner:
            return
        self.log('load banner')
        banner = self.query_one('.banner', SixelImage)

        banner.image = get_and_maybe_write(self.user.banner)
        banner.loading = False

    @work(thread=True, exclusive=True)
    def load_user(self):
        self.log('load user')
        self.user.refresh()
        self.refresh(recompose=True)
        self.call_after_refresh(self.load_banner)

    def on_mount(self):
        # self.query_one('.user-info').loading = True
        self.query_one('.banner').loading = True
        if self.user.banner:
            self.load_banner()

        posts = self.query_one(PostsWidget)
        if not posts.posts:
            posts.load_posts()
