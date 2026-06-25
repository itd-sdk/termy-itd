from itd import Clan, Hashtag, Hashtags, TopClans, User
from itd.user import WhoToFollow
from textual import work
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Click
from textual.widgets import Button, Input, Static

from app.screens.base import BaseScreen
from app.widgets.shared import Avatar, DisplayName


class HashtagWidget(Horizontal):
    def __init__(self, place: int, hashtag: Hashtag):
        super().__init__()
        self.hashtag = hashtag
        self.place = place

    def compose(self):
        yield Static(str(self.place), classes='place')
        yield Static(f'#{self.hashtag.name}')
        yield Static(str(self.hashtag.posts_count), classes='count')

    def on_click(self):
        self.notify('todo', severity='error')


class ClanWidget(Horizontal):
    def __init__(self, place: int, clan: Clan):
        super().__init__()
        self.clan = clan
        self.place = place

    def compose(self):
        yield Static(str(self.place), classes='place')
        yield Static(self.clan.avatar)
        yield Static(str(self.clan.members_count), classes='count')

    def on_click(self):
        self.notify('todo', severity='error')
        # self.app.open_url('https://itdsdk.qzz.io/ebdi')


class UserWidget(Horizontal):
    def __init__(self, place: int, user: User):
        super().__init__()
        self.user = user
        self.place = place

    def compose(self):
        yield Avatar(self.user, clickable=False, classes='place')
        with Vertical():
            yield DisplayName(self.user, clickable=False)
            yield Static(f'@{self.user.username}', classes='username')
        yield Static(str(self.user.followers_count), classes='count')

    async def on_click(self, event: Click):
        event.stop()
        await self.query_one(DisplayName).on_click(event)


class SearchScreen(BaseScreen):
    screen_name = 'search'
    CSS_PATH = '../css/search.tcss'

    def compose(self):
        yield from super().compose()

        yield Input(placeholder='Поиск и тд')
        with Horizontal():
            with Vertical():
                yield Static('Топ хэштэгов', classes='h1')
                yield VerticalScroll(id='hashtags')

            with Vertical():
                yield Static('Топ кланов', classes='h1')
                yield VerticalScroll(id='clans')

            with Vertical():
                yield Static('Топ пользователей', classes='h1')
                yield Vertical(id='users')

    @work(thread=True, exclusive=True)
    def load_hashtags(self):
        hashtags = self.query_one('#hashtags', VerticalScroll)
        self.app.call_from_thread(hashtags.set_loading, True)

        for i, hashtag in enumerate(Hashtags()):
            self.app.call_from_thread(hashtags.mount, HashtagWidget(i, hashtag))

        self.app.call_from_thread(hashtags.set_loading, False)

    @work(thread=True, exclusive=True)
    def load_clans(self):
        clans = self.query_one('#clans', VerticalScroll)
        self.app.call_from_thread(clans.set_loading, True)

        for i, clan in enumerate(TopClans()):
            self.app.call_from_thread(clans.mount, ClanWidget(i, clan))

        self.app.call_from_thread(clans.set_loading, False)

    @work(thread=True, exclusive=True)
    def load_users(self):
        users = self.query_one('#users', Vertical)
        self.app.call_from_thread(users.set_loading, True)

        for i, user in enumerate(WhoToFollow()):
            self.app.call_from_thread(users.mount, UserWidget(i, user))
        self.app.call_from_thread(users.mount, Button('Весь топ'))

        self.app.call_from_thread(users.set_loading, False)

    def on_mount(self):
        self.load_clans()
        self.load_hashtags()
        self.load_users()

    def on_button_pressed(self, event: Button.Pressed):
        self.app.open_url('https://itdsdk.qzz.io/ebdi')
