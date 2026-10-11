from enum import Enum
from typing import TYPE_CHECKING

from itd import ITDClient, ITDConfig, init_client
from itd.core.auth import AccessAuth, RefreshAuth
from itd.core.qr import QRLogin
from itd.exceptions import AccessTokenExpiredError, SessionExpiredError, SessionNotFoundError, SessionRevokedError
from textual import work
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Input, LoadingIndicator, Static
from textual_englyph import EnGlyphText
from textual_nav import NavPage

from app.widgets.qr import QRWidget

if TYPE_CHECKING:
    from app.main import TermyITDApp


class AuthOption(Horizontal):
    class Clicked(Message):
        def __init__(self, state: State):
            super().__init__()
            self.state = state

    def __init__(self, state: State, label: str):
        super().__init__()
        self.label = label
        self.state = state
        self.disabled = state == State.creds

    def compose(self):
        yield Static(self.label)
        yield Static('')

    def on_click(self, event):
        self.post_message(self.Clicked(self.state))


class State(Enum):
    start = 'start'
    refresh = 'refresh'
    access = 'access'
    qr = 'qr'
    creds = 'creds'
    no = 'no'


class LoginPage(NavPage, tab_name='login'):
    BINDINGS = [Binding('escape', 'back')]
    app: 'TermyITDApp'
    # CSS_PATH = '../css/login.tcss'

    state: reactive[State] = reactive(State.start, recompose=True)
    qr_status: reactive[str] = reactive('pending', recompose=True)
    qr: QRLogin | None = None
    client: ITDClient | None = None

    def compose(self):
        with Vertical(id='container'):
            with Center():
                yield EnGlyphText('ИТД', font_name='casio-fx-9860gii.ttf', font_size=6, basis=(1, 2))

            if self.state == State.start:
                yield AuthOption(State.qr, 'Войти по QR коду')
                yield Static('━' * (self.size.width // 2 - 4), classes='divider')
                yield AuthOption(State.refresh, 'Войти через refresh токен')
                yield Static('━' * (self.size.width // 2 - 4), classes='divider')
                yield AuthOption(State.access, 'Войти через access токен')
                # yield Static(classes='divider')
                # yield AuthOption(State.creds, 'Войти по email & паролю')
                # yield Static('━' * (self.size.width // 2 - 4), classes='divider', id='no-auth-divider')
                # yield AuthOption(State.no, 'Продолжить без авторизации')

            if self.state == State.access:
                yield Static('[b]ВНИМАНИЕ:[/b] авторизация через access токен будет действовать только ~15 минут.', id='access-warn')
                yield Input(placeholder='access токен', id='access')
                yield Static(classes='error')
                with Center():
                    yield Button('Войти', variant='primary', disabled=True)

            if self.state == State.refresh:
                yield Input(placeholder='refresh токен', id='refresh')
                yield Static(classes='error')
                with Center():
                    yield Button('Войти', variant='primary', disabled=True)

            if self.state == State.qr:
                if self.qr is None:
                    with Center():
                        yield LoadingIndicator()
                else:
                    assert self.qr.qr
                    with Center():
                        yield Static('Отсканируйте QR код в приложении', classes='qr-text')
                    with Center():
                        yield QRWidget(self.qr.qr.payload)
                    with Center():
                        yield Static(self.qr.qr.payload, classes='qr-text dim')
                    if self.qr_status and self.qr_status != 'pending':
                        status: tuple[str, str] = {
                            'authorized': ('QR код авторизован', 'success qr-text'),
                            'approved': ('QR одобрен: авторизация..', 'qr-text'),
                            'scanned': ('QR код отсканирован', 'qr-text'),
                            'rejected': ('QR код отклонен', 'error qr-text'),
                            'expired': ('Срок сканирования истек', 'error qr-text')
                        }[self.qr_status]
                        with Center():
                            yield Static(status[0], classes=status[1])

                    if self.qr_status == 'authorized':
                        with Center():
                            yield Button('Войти', variant='primary', id='auth-qr')

                    if self.qr_status in ('expired', 'rejected'):
                        with Center():
                            yield Button('Обновить', variant='error', id='refresh-qr')

    def on_input_changed(self, event: Input.Changed):
        self.query_one(Button).disabled = not bool(event.input.value)

    def on_button_pressed(self, event: Button.Pressed):
        #     self._on_button_pressed(event)

        # @work(thread=True, exclusive=True)
        # def _on_button_pressed(self, event: Button.Pressed):
        if event.button.id == 'refresh-qr':
            assert self.qr
            self._refresh_qr()
            return

        try:
            if event.button.id != 'auth-qr':
                self.app.client = init_client(
                    'termy-itd',
                    auth=RefreshAuth(self.query_one('#refresh', Input).value)
                    if self.state == State.refresh
                    else AccessAuth(self.query_one('#access', Input).value),
                    config=ITDConfig(
                        'client',
                        timeout=10,
                        timeout_file=30,
                        post_update_stats=False,
                        post_view_increment=True,
                        load_on_iter=None,
                        load_on_getattr=False,
                        dwell_check_active=False
                    )
                )
            else:
                assert self.qr
                self.app.client = self.qr.get_client(
                    'termy-itd',
                    config=ITDConfig(  # todo куда нибудь вынести отдельно чтобы не дублировалось с мейном
                        'client',
                        timeout=10,
                        timeout_file=30,
                        post_update_stats=False,
                        post_view_increment=True,
                        load_on_iter=None,
                        load_on_getattr=False,
                        dwell_check_active=False
                    )
                )
        except SessionNotFoundError:
            self.query_one('.error', Static).content = 'Токен не найден'
        except SessionRevokedError:
            self.query_one('.error', Static).content = 'Токен ревокнут (выход из аккаунта)'
        except AccessTokenExpiredError, SessionExpiredError:
            self.query_one('.error', Static).content = 'Токен истек'
        else:
            self.app.nav_visible = True
            self.switch('Главная')

    def on_auth_option_clicked(self, event: AuthOption.Clicked):
        self.state = event.state
        if self.state == State.qr:
            self._refresh_qr()

    @work(thread=True, exclusive=True)
    def _refresh_qr(self):
        self.qr = QRLogin()
        self.qr_status = 'pending'
        self.app.call_from_thread(self.refresh, recompose=True)
        self.stream_qr()

    @work(thread=True, exclusive=True)
    def stream_qr(self):
        assert self.qr
        for event in self.qr.events():
            self.notify(event)
            self.qr_status = event

    def action_back(self):
        self.state = State.start
