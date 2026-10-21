from itd import User
from itd.enums import LoadStatus
from textual import work
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import LoadingIndicator, Static
from textual_image.widget import SixelImage
from textual_nav import NavPage

from app.cache import get_and_maybe_write
from app.widgets import PostsScroll, PostsWidget
from app.widgets.shared import Avatar, ClickableStatic, DisplayName


class Counter(ClickableStatic):
    def __init__(self, name: str, value: int):
        super().__init__(f'{value} [$foreground-muted]{name}[/]')
        self.counter_name = name
        self.counter_value = value


class UserPage(NavPage, tab_name='Профиль', tab_icon=''):
    # CSS_PATH = '../css/user.tcss'
    BINDINGS = [Binding('escape', 'pop', 'Назад'), Binding('f5', 'refresh', 'Обновить')]

    def __init__(self, user: User | None = None):
        super().__init__()
        self.user = user or User(self.app.client.user_id)  # ty: ignore
        self.log(f'open user screen username={user.username if user else "me"}')
        if user is None:
            self.screen_name = 'profile'

    def compose(self):
        yield from super().compose()

        if self.user.load_status != LoadStatus.FULL:
            yield LoadingIndicator()  # я займу все место и тд
            return

        with PostsScroll():
            yield SixelImage(on_error=lambda _: Static('Ошибка обработки банера', classes='attach-error'), classes='banner')

            with Vertical(classes='user-info'):
                with Horizontal():
                    yield Avatar(self.user, clickable=False, classes='blue' if self.user.is_subscribed else '')
                    with Vertical():
                        with Horizontal():
                            self.log(self.user.event_profile.curtains.available)
                            yield DisplayName(self.user, clickable=False)
                            yield Static(f'@{self.user.username}', classes='user-info-username')

                        if self.user.bio:
                            yield Static(self.user.bio, classes='bio')

                        with Horizontal(classes='user-extra-info'):
                            if self.user.online:
                                yield Static('Онлайн', classes='online')
                            elif self.user.last_seen:
                                yield Static(f'Был {self.user.last_seen}', classes='last-seen')
                            else:
                                yield Static('Был хз когда', classes='last-seen')

                            yield Static(
                                f'[b]Мелки:[/b] [{"green" if self.user.event_profile.curtains.available else "red"}]{self.user.event_profile.curtains.amount}/100[/]',
                                classes='user-curtains-donate'
                            )
                            # 0-20  17 тлеет red
                            # 20-45  34 41 мерцает orange
                            # 45-65  45 62 ровная yellow
                            # 65-85  67 84 светится green
                            # 85-100 85 97 сияет cyan

                            aura = self.user.event_profile.aura
                            if aura:
                                color = 'red' if aura <= 20 else 'orange' if aura <= 45 else 'yellow' if aura <= 65 else 'green' if aura <= 85 else 'cyan'
                                name = {'red': 'Тлеет', 'orange': 'Мерцает', 'yellow': 'Ровная', 'green': 'Светится', 'cyan': 'Сияет'}[color]
                                yield Static(f'[b]Аура:[/b] [{color}]{aura}[/] - [{color} italic]{name}[/]')

                            if self.user.event_profile.curtains.closed:
                                yield Static('Шторы закрыты', classes='error')

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
        self.app.call_from_thread(banner.set_loading, True)
        banner.image = get_and_maybe_write(self.user.banner)
        self.app.call_from_thread(banner.set_loading, False)

    @work(thread=True, exclusive=True)
    def load_user(self):
        self.log('load user')
        self.user.refresh()
        self.user.event_profile.refresh()
        self.refresh(recompose=True)
        self.app.call_from_thread(self.set_timer, 0.5, self.load_banner)  # todo # p.s call_after_refresh not works
        if not self.user.posts:
            self.call_after_refresh(lambda: self.query_one(PostsWidget).load_posts())

    @work(thread=True, exclusive=True)
    def refresh_user(self):
        self.log('refresh user')
        self.user.load_status = LoadStatus.NO
        self.refresh(recompose=True)

        self.user.refresh()
        self.refresh(recompose=True)

        self.call_after_refresh(self.load_banner)
        self.call_after_refresh(lambda: self.query_one(PostsWidget).action_refresh())
        self.call_after_refresh(self.focus)

    def on_mount(self):
        if self.user.load_status != LoadStatus.FULL:
            self.load_user()
            return

        if self.user.banner:
            self.load_banner()
        if not self.user.posts:
            self.query_one(PostsWidget).load_posts()
        self.focus()

    def action_refresh(self):
        self.refresh_user()

    def action_pop(self):
        self.pop()
