from webbrowser import open

from itd import Post
from pyperclip import copy
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from app.dialogs import CarouselDialog, ConfirmDialog, RepostDialog
from app.widgets.shared import ClickableStatic, ImageCarousel


def _compose_post(post: Post, original_post: bool = True) -> ComposeResult:
    with Horizontal(classes='post-top'):
        yield Static(post.author.avatar, classes='avatar')
        with Vertical():
            with Horizontal(classes='display-name'):
                yield Static(post.author.display_name, classes='subscribed' if post.author.is_subscribed else '', markup=False)
                if post.author.verified:
                    yield Static('', classes='verified')
            yield Static(f'@{post.author.username}', classes='username')
        yield Static(post.created_at.strftime('%d.%m.%y %H:%M:%S'), classes='date')
        with Horizontal(classes='actions'):
            yield ClickableStatic('󰒗', classes='share')
            yield ClickableStatic('', classes='copy')
            if not post.is_owner:
                yield ClickableStatic('', classes='report')
            else:
                yield ClickableStatic('', classes='pin')
                yield ClickableStatic('󰆴', classes='delete')

    yield Static(post.content)

    if post.attachments:
        yield ImageCarousel(post.attachments)

    if original_post and post.original_post is not None:
        yield OriginalPostWidget(post.original_post)

    with Horizontal(classes='stats'):
        yield ClickableStatic(f'{"" if post.is_liked else ""} {post.likes_count}', classes=f'likes{" active" if post.is_liked else ""}')
        yield ClickableStatic(f' {post.comments_count}', classes='comments')
        yield ClickableStatic(f'󰑖 {post.reposts_count}', classes=f'reposts{" active" if post.is_reposted else ""}')
        if post.dominant:
            yield Static(post.dominant, classes='dominant')
        yield Static(f' {post.views_count}', classes=f'views{" active" if post.is_viewed else ""}{" only" if post.dominant is None else ""}')


class PostWidget(Widget):
    can_focus = True
    BINDINGS = [
        Binding('a', 'open_attachments', 'Открыть вложения'),
        Binding('l', 'like', 'Лайк'),
        Binding('r', 'repost', 'Репост'),
        Binding('ctrl+c', 'copy', 'Скопировать текст'),
        Binding('u', 'copy_url', 'Скопировать ссылку на пост'),
        Binding('U', 'open_url', 'Открыть пост в браузере'),
        Binding('p', 'pin', 'Закрепить пост'),
        Binding('delete', 'delete', 'Удалить пост'),
        Binding('alt+r', 'report', 'Пожаловаться'),
        Binding('enter', 'open', 'Открыть пост'),
        Binding('f', 'focus_original_post', 'Сфокусироваться на оригинальном посте')
    ]

    def __init__(self, post: Post):
        super().__init__(classes='post')
        self.post = post
        self.view_started_at: int | None = None
        self.view_ended_at: int | None = None
        self.seen_bottom: bool = False

    def compose(self) -> ComposeResult:
        yield from _compose_post(self.post)

    def action_open_attachments(self):
        if self.post.attachments:
            self.app.push_screen(CarouselDialog(self.post.attachments))
        elif self.post.original_post and self.post.original_post.attachments:
            self.query_one(OriginalPostWidget).action_open_attachments()
        else:
            self.notify('Нет вложений', severity='warning')

    def action_focus_original_post(self):
        if self.post.original_post is not None:
            self.query_one(OriginalPostWidget).focus()
        else:
            self.notify('Нет оригинального поста', severity='warning')

    def action_like(self):
        button = self.query_one('.likes', ClickableStatic)

        if self.post.is_liked:
            button.remove_class('active')
            self.post.unlike()
            button.update(f' {self.post.likes_count}')
        else:
            button.add_class('active')
            self.post.like()
            button.update(f' {self.post.likes_count}')

    def action_repost(self):
        def repost(text: str | None = None):
            if text is None:
                return

            button = self.query_one('.reposts', ClickableStatic)
            button.add_class('active')
            self.post.repost(text)
            self.notify('Пост репостнут')
            button.update(f'󰑖 {self.post.reposts_count}')

        self.app.push_screen(RepostDialog(), repost)

    def action_copy(self):
        if self.post.content:
            copy(self.post.content)
            self.notify('Текст поста скопирован')
        else:
            self.notify('Нечего копировать', severity='warning')

    def action_copy_url(self):
        copy(self.post.url)
        self.notify('Ссылка на пост скопирована')

    def action_open_url(self):
        open(self.post.url)
        self.notify('Пост должен открыться в браузере')

    def action_pin(self):
        self.app.push_screen(ConfirmDialog('Закрепление', 'Действительно закрепить пост?'))

    def action_delete(self):
        self.app.push_screen(ConfirmDialog('Удаление', 'Действительно удалить пост?'))

    def action_report(self):
        self.notify('todo', severity='error')

    def on_clickable_static_clicked(self, event: ClickableStatic.Clicked):
        event.stop()
        if 'like' in event.classes:
            self.action_like()
        if 'repost' in event.classes and not self.post.is_reposted:
            self.action_repost()
        if 'copy' in event.classes:
            self.action_copy()
        if 'share' in event.classes:
            self.action_copy_url()
        if 'pin' in event.classes:
            self.action_pin()
        if 'delete' in event.classes:
            self.action_delete()
        if 'report' in event.classes:
            self.action_report()

    def on_original_post_widget_repost_focused(self, event: OriginalPostWidget.RepostFocused):
        self.focus()

    def check_is_visible(self):
        if self.view_started_at and self.view_ended_at:
            return

        top_visible = self.screen.region.contains_point(self.region.top_right)
        bottom_visible = self.screen.region.contains_point(self.region.bottom_left)

        if not self.seen_bottom and bottom_visible:
            self.seen_bottom = True

        if top_visible:
            self.post.set_visible()

        elif self.seen_bottom and not top_visible and not bottom_visible:
            self.timer.stop()
            self.post.set_invisible()

            views = self.query_one('.views', Static)
            views.update(f' {self.post.views_count}')
            views.add_class('active')

    def on_mount(self):
        self.timer = self.set_interval(0.1, self.check_is_visible)

    def on_click(self, event: Click):
        if event.chain >= 2:
            event.stop()
            self.action_open()

    def action_open(self):
        from app.screens import PostScreen  # stupid circular import

        self.app.push_screen(PostScreen(self.post))


class OriginalPostWidget(PostWidget, inherit_bindings=False):
    BINDINGS = PostWidget.BINDINGS[:-1] + [Binding('f', 'focus_repost', 'Сфокусироваться на репосте')]

    class RepostFocused(Message):
        pass

    def action_focus_repost(self):
        self.post_message(self.RepostFocused())

    def action_focus_original_post(self):
        pass

    def compose(self) -> ComposeResult:
        yield from _compose_post(self.post, original_post=False)
