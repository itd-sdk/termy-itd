from typing import cast

from itd import Clan, Hashtag, Hashtags, TopClans, User
from itd.user import WhoToFollow
from textual import work
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.events import Click
from textual.widgets import Button, ContentSwitcher, Input, Static

from app.screens.base import BaseScreen
from app.screens.user import UserScreen
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

    def on_click(self, event: Click):
        event.stop()
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

    def on_click(self, event: Click):
        event.stop()
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
        self.log('usrwdg')
        event.stop()
        await self.app.push_screen(UserScreen(self.user))


class SearchScreen(BaseScreen):
    screen_name = 'search'
    CSS_PATH = '../css/search.tcss'

    def compose(self):
        yield from super().compose()

        with Horizontal():
            yield Input(placeholder='Поиск и тд')
            yield Button(' ', id='search-button')

        with ContentSwitcher(initial='overview'):
            with Horizontal(id='overview'):
                with Vertical():
                    yield Static('Топ хэштэгов', classes='h1')
                    yield VerticalScroll(id='hashtags')

                with Vertical():
                    yield Static('Топ кланов', classes='h1')
                    yield VerticalScroll(id='clans')

                with Vertical():
                    yield Static('Топ пользователей', classes='h1')
                    yield Vertical(id='users')

            with Horizontal(id='search'):
                with Vertical():
                    yield Static('Пользователи', classes='h1')
                    yield VerticalScroll(id='search-users')

                with Vertical():
                    yield Static('Хэштэги', classes='h1')
                    yield VerticalScroll(id='search-hashtags')

            yield Container(id='empty')

    @work(thread=True, exclusive=True)
    def load_hashtags(self):
        self.log('load hashtags')
        hashtags = self.query_one('#hashtags', VerticalScroll)
        self.app.call_from_thread(hashtags.set_loading, True)

        for i, hashtag in enumerate(Hashtags()):
            self.app.call_from_thread(hashtags.mount, HashtagWidget(i, hashtag))

        self.app.call_from_thread(hashtags.set_loading, False)

    @work(thread=True, exclusive=True)
    def load_clans(self):
        self.log('load clans')
        clans = self.query_one('#clans', VerticalScroll)
        self.app.call_from_thread(clans.set_loading, True)

        for i, clan in enumerate(TopClans()):
            self.app.call_from_thread(clans.mount, ClanWidget(i, clan))

        self.app.call_from_thread(clans.set_loading, False)

    @work(thread=True, exclusive=True)
    def load_users(self):
        self.log('load top users')
        users = self.query_one('#users', Vertical)
        self.app.call_from_thread(users.set_loading, True)

        for i, user in enumerate(WhoToFollow()):
            self.app.call_from_thread(users.mount, UserWidget(i, user))
        self.app.call_from_thread(users.mount, Button('Весь топ', id='all-top'))

        self.app.call_from_thread(users.set_loading, False)

    def on_mount(self):
        self.load_clans()
        self.load_hashtags()
        self.load_users()

    def on_button_pressed(self, event: Button.Pressed):
        event.stop()
        if event.button.id == 'all-top':
            self.app.open_url('https://itdsdk.qzz.io/ebdi')
        elif event.button == 'search-button':
            self.search()

    def on_input_changed(self, event: Input.Changed):
        event.stop()
        switcher = self.query_one(ContentSwitcher)
        if switcher.current == 'overview':
            switcher.current = 'empty'
        if switcher.current == 'search' and not event.value.strip():
            switcher.current = 'overview'

    def on_input_submitted(self, event: Input.Submitted):
        event.stop()
        if event.value:
            self.query_one(ContentSwitcher).current = 'search'
            self.search()

    def search(self):
        users, hashtags = cast(tuple[list[User], list[Hashtag]], self.app.client.search(self.query_one(Input).value))  # ty: ignore

        users_widget = self.query_one('#search-users', VerticalScroll)
        hashtags_widget = self.query_one('#search-hashtags', VerticalScroll)
        users_widget.remove_children()
        hashtags_widget.remove_children()

        for i, user in enumerate(users):
            users_widget.mount(UserWidget(i, user))

        for i, hashtag in enumerate(hashtags):
            hashtags_widget.mount(HashtagWidget(i, hashtag))
