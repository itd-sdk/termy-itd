from itd import ITDClient, ITDConfig, Notifications, init_client
from itd.core.logger import setup_logging
from itd.exceptions import AccessTokenExpiredError, InsufficientAuthLevelError, SessionExpiredError, SessionNotFoundError, SessionRevokedError
from itd.models.notification import Notification
from textual import work
from textual.logging import TextualHandler
from textual_nav import NavApp

from app.screens import HomePage, LoginPage, NotificationsPage, SearchPage, UserPage
from app.widgets.navbar import TermyNavigationDrawer

setup_logging('debug', colorful=True).addHandler(TextualHandler())


class TermyITDApp(NavApp):
    CSS_PATH = [
        'css/style.tcss',
        'css/post.tcss',
        'css/comment.tcss',
        'css/notification.tcss',
        'css/login.tcss',
        'css/search.tcss',
        'css/user.tcss'
    ]  # https://github.com/Textualize/textual/discussions/4509
    PAGES = [HomePage, NotificationsPage, SearchPage, UserPage]
    NAV_TYPE = TermyNavigationDrawer
    client: ITDClient  # = init_client('termy-itd')
    page_visible = False  # do not show home page by init because we need to check is client working, then decide go login or home

    def __init__(self, ansi_color: bool = False):
        super().__init__(ansi_color=ansi_color)
        self.log('init')

    def update_notifications_count(self, count: int | None = None):
        count = count or self.notifications.unread_count
        self.log(f'update notifications count count={count}')
        if count == 0:
            title = '  Уведомления'
        else:
            title = f' Уведомления [white on red]{count}[/]'

        # for screen in self.screens:
        #     screen.query_one('.notifications-tab', ClickableStatic).update(title)

    def on_mount(self, event):  # ty: ignore
        self.log('app.mount')

        try:
            self.client = init_client(
                'termy-itd',
                config=ITDConfig(
                    'client',
                    timeout=10,
                    timeout_file=30,
                    post_update_stats=False,
                    post_view_increment=True,
                    load_on_iter=None,
                    load_on_getattr=False,
                    dwell_check_active=False,
                    interactive_auth=False
                )
            )
            self.client.user.refresh()
        except SessionExpiredError:
            self.log.error('app.mount session expired')
            self.notify('Сессия истекла', severity='error')
        except SessionNotFoundError:
            self.log.error('app.mount session not found')
            self.notify('Сессия не найдена', severity='error')
        except SessionRevokedError:
            self.log.error('app.mount session revoked')
            self.notify('Сессия ревокнута (выход из аккаунта)', severity='error')
        except AccessTokenExpiredError:
            self.log.error('app.mount access token expired')
            self.notify('access токен истек', severity='error')
        except InsufficientAuthLevelError:
            self.log.error('app.mount insufficient auth level')
            pass  # need to login
        else:
            self.log('app.mount startup')
            self.startup()
            return

        event.prevent_default()
        self.log('app.mount login')
        self.nav_visible = False
        self.page_visible = True
        self.switch_page(LoginPage())

        # self.push_page(LoginPage(), lambda client: self.startup(client))

    def startup(self):
        self.log(f'app.startup auth={self.client.auth_level.value}')
        self.page_visible = True

        self.call_after_refresh(self.init_ntfs)

    @work(thread=True, exclusive=True)
    def init_ntfs(self):
        self.log('app.init_ntfs')
        self.notifications = Notifications()

        @self.notifications.on()
        def _on_notification(self, notification: Notification):
            self.log(f'app.ntf_call type={notification.type.value}')
            # self.update_notifications_count(self.notifications.unread_count)
            self.notify(
                notification.preview or notification.get_text(avatar=True),
                title=notification.get_text(avatar=True) if notification.preview else 'Новое уведомление',
                timeout=15
            )
            # if self.is_screen_installed('notifications'):
            #     self.get_screen('notifications')._add_notification(notification)

        self.notifications.unread_count
        self.notifications.stream_bg(True)
        self.update_notifications_count()


app = TermyITDApp(ansi_color=False)
app.run()
