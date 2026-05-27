from typing import Iterable
from webbrowser import open

from PIL import Image as PILImage, UnidentifiedImageError
from pyperclip import copy
from textual import work
from textual.binding import Binding
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import HorizontalScroll, Horizontal, Vertical
from textual_image.widget import HalfcellImage
from textual_image.renderable.halfcell import Image as HalfcellRenderable
from itd import Post
from itd.file import PostAttach
from itd.enums import AttachType

from app.dialogs import RepostDialog, CarouselDialog, ConfirmDialog
from app.cache import get_and_maybe_write


class Image(HalfcellImage, Renderable=HalfcellRenderable):
    class Clicked(Message):
        def __init__(self, idx: int) -> None:
            super().__init__()
            self.idx = idx

    class Failed(Message):
        def __init__(self, idx: int) -> None:
            super().__init__()
            self.idx = idx

    def __init__(self, image: PostAttach, idx: int) -> None:
        super().__init__(classes='image')
        self.attachment = image
        self.loading = True
        self.idx = idx

    @work(thread=True)
    def load_image(self):
        image = get_and_maybe_write(self.attachment)
        try:
            PILImage.open(image).verify()
        except (UnidentifiedImageError, OSError):
            self.app.call_from_thread(self.post_message, self.Failed(self.idx))
        else:
            self.image = image
        finally:
            self.loading = False

    def on_mount(self):
        self.load_image()

    def on_click(self):
        self.post_message(self.Clicked(self.idx))


class ImageCarousel(HorizontalScroll):
    failed_ids: reactive[list[int]] = reactive([], recompose=True)

    def __init__(self, attachments: list[PostAttach]) -> None:
        super().__init__(classes='images')
        self.attachments = attachments

    def compose(self) -> ComposeResult:
        for i, attachment in enumerate(self.attachments):
            if i in self.failed_ids:
                yield Static('Не удалось обработать вложение', classes='attach-error')
            elif attachment.type == AttachType.IMAGE:
                yield Image(attachment, i)
            elif attachment.type == AttachType.VIDEO:
                yield Static('[VIDEO]')
            elif attachment.type == AttachType.AUDIO:
                yield Static('[AUDIO]')
            else:
                yield Static('[MEDIA]')

    def on_image_clicked(self, event: Image.Clicked):
        event.stop()
        self.app.push_screen(CarouselDialog(self.attachments, event.idx))

    def on_image_failed(self, event: Image.Failed):
        event.stop()
        self.failed_ids = [*self.failed_ids, event.idx]



class ClickableStatic(Static):
    class Clicked(Message):
        def __init__(self, classes: str | frozenset[str] | Iterable[str]) -> None:
            super().__init__()
            if isinstance(classes, (frozenset, Iterable)):
                classes = list(classes)
                if not classes:
                    self.classes = ''
                else:
                    if 'active' in classes:
                        classes.remove('active')
                    self.classes = classes[0]
            else:
                self.classes = classes

    def __init__(self, content: str = "", *, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(content, id=id, classes=classes)

    def on_click(self):
        if self.classes:
            self.post_message(self.Clicked(self.classes))


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
        Binding('f', 'focus_original_post', 'Сфокусироваться на оригинальном посте'),
        # Binding('escape', 'blur', 'Расфокусироваться') # Мишка, РАСФОКУСИРУЙ МЕНЯЯЯ 😭😭😭
    ]

    def __init__(self, post: Post):
        super().__init__(classes='post')
        self.post = post
        self.view_started_at: int | None = None
        self.view_ended_at: int | None = None
        self.seen_bottom: bool = False

    def compose(self) -> ComposeResult:
        with Horizontal(classes='author'):
            yield Static(self.post.author.avatar, classes='author-avatar')
            with Vertical(classes='author-name'):
                with Horizontal(classes='author-display'):
                    yield Static(self.post.author.display_name, classes='subscribed' if self.post.author.is_subscribed else '')
                    if self.post.author.verified:
                        yield Static('', classes='verified')
                yield Static(f'@{self.post.author.username}', classes='author-username')
            yield Static(self.post.created_at.strftime('%d.%m.%y %H:%M:%S'), classes='date')
            with Horizontal(classes='actions'):
                yield ClickableStatic('󰒗', classes='share')
                yield ClickableStatic('', classes='copy')
                if not self.post.is_owner:
                    yield ClickableStatic('', classes='report')
                else:
                    yield ClickableStatic('', classes='pin')
                    yield ClickableStatic('󰆴', classes='delete')

        yield Static(self.post.content)

        if self.post.attachments:
           yield ImageCarousel(self.post.attachments)

        if self.post.original_post is not None:
            yield OriginalPostWidget(self.post.original_post)

        with Horizontal(classes='stats'):
            yield ClickableStatic(f'{"" if self.post.is_liked else ""} {self.post.likes_count}', classes=f'likes{" active" if self.post.is_liked else ""}')
            yield ClickableStatic(f' {self.post.comments_count}', classes='comments')
            yield ClickableStatic(f'󰑖 {self.post.reposts_count}', classes=f'reposts{" active" if self.post.is_reposted else ""}')
            if self.post.dominant:
                yield Static(self.post.dominant, classes='dominant')
            yield Static(f' {self.post.views_count}', classes=f'views{" active" if self.post.is_viewed else ""}{" only" if self.post.dominant is None else ""}')


    def action_open_attachments(self):
        if self.post.attachments:
            self.app.push_screen(CarouselDialog(self.post.attachments))
        elif self.post.original_post and self.post.original_post.attachments:
            self.query_one(OriginalPostWidget).action_open_attachments()
        else:
            self.notify('Нет вложений', severity='warning')

    def action_focus_original_post(self):
        if self.post.original_post:
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
            button.update(f' {self.post.likes_count}')

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


class OriginalPostWidget(PostWidget, inherit_bindings=False):
    BINDINGS = PostWidget.BINDINGS[:-1] + [Binding('f', 'focus_repost', 'Сфокусироваться на репосте')]

    class RepostFocused(Message):
        pass

    def action_focus_repost(self):
        self.post_message(self.RepostFocused())

    def compose(self) -> ComposeResult:
        with Horizontal(classes='author'):
            yield Static(self.post.author.avatar, classes='author-avatar')
            with Vertical(classes='author-name'):
                with Horizontal(classes='author-display'):
                    yield Static(self.post.author.display_name, classes='subscribed' if self.post.author.is_subscribed else '')
                    if self.post.author.verified:
                        yield Static('', classes='verified')
                yield Static(f'@{self.post.author.username}', classes='author-username')
            yield Static(self.post.created_at.strftime('%d.%m.%y %H:%M:%S'), classes='date')
            with Horizontal(classes='actions'):
                yield Static('󰒗', classes='share')
                yield Static('', classes='copy')
                yield Static('', classes='report')

        yield Static(self.post.content)

        if self.post.attachments:
            yield ImageCarousel(self.post.attachments)


        with Horizontal(classes='stats'):
            yield ClickableStatic(f'{"" if self.post.is_liked else ""} {self.post.likes_count}', classes=f'likes{" active" if self.post.is_liked else ""}')
            yield ClickableStatic(f' {self.post.comments_count}', classes='comments')
            yield ClickableStatic(f'󰑖 {self.post.reposts_count}', classes=f'reposts{" active" if self.post.is_liked else ""}')
            if self.post.dominant:
                yield ClickableStatic(self.post.dominant, classes='dominant')
            yield Static(f' {self.post.views_count}', classes=f'views{" active" if self.post.is_viewed else ""}{" only" if self.post.dominant is None else ""}')
