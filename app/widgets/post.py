from PIL import Image as PILImage, UnidentifiedImageError
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

from app.dialogs import RepostDialog, CarouselDialog
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
        except UnidentifiedImageError:
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
        def __init__(self, id: str) -> None:
            super().__init__()
            self.id = id

    def __init__(self, content: str = "", *, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(content, id=id, classes=classes)

    def on_click(self):
        if self.id:
            self.post_message(self.Clicked(self.id))


class PostWidget(Widget):
    BINDINGS = [
        Binding('a', 'open_attachments', 'Открыть вложения'),
        Binding('l', 'like', 'Лайк'),
        Binding('r', 'repost', 'Репост'),
    ]
    def __init__(self, post: Post):
        super().__init__(classes='post')
        self.post = post

    def compose(self) -> ComposeResult:
        with Horizontal(classes='author'):
            yield Static(self.post.author.avatar, classes='author-avatar')
            with Vertical(classes='author-name'):
                with Horizontal(classes='author-display'):
                    yield Static(self.post.author.display_name, classes='subscribed' if self.post.author.is_subscribed else '')
                    if self.post.author.verified:
                        yield Static('', classes='verified')
                yield Static(f'@{self.post.author.username}', classes='author-username')
            with Horizontal(classes='actions'):
                yield Static('󰒗', classes='share')
                yield Static('', classes='copy')
                if not self.post.is_owner:
                    yield Static('', classes='report')
                else:
                    yield Static('', classes='pin')
                    yield Static('󰆴', classes='delete')

        yield Static(self.post.content)

        if self.post.attachments:
           yield ImageCarousel(self.post.attachments)

        if self.post.original_post:
            yield OriginalPostWidget(self.post.original_post)

        with Horizontal(classes='stats'):
            yield ClickableStatic(f'{"" if self.post.is_liked else ""} {self.post.likes_count}', classes=f'likes{" active" if self.post.is_liked else ""}', id='like')
            yield ClickableStatic(f' {self.post.comments_count}', classes='comments', id='comment')
            yield ClickableStatic(f'󰑖 {self.post.reposts_count}', classes=f'reposts{" active" if self.post.is_liked else ""}', id='repost')
            yield ClickableStatic(f' {self.post.views_count}', classes=f'views{" active" if self.post.is_viewed else ""}', id='view')


    def action_open_attachments(self):
        self.app.push_screen(CarouselDialog(self.post.attachments))

    def action_focus_original_post(self):
        if self.post.original_post:
            self.query_one(OriginalPostWidget).focus()
        else:
            self.notify('Нет оригинального поста', severity='warning')

    def action_like(self):
        button = self.query_one('#like', ClickableStatic)

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

            button = self.query_one('#repost', ClickableStatic)
            button.add_class('active')
            self.post.repost(text)
            self.notify('Пост репостнут')
            button.update(f'󰑖 {self.post.reposts_count}')

        self.app.push_screen(RepostDialog(), repost)


    def on_clickable_static_clicked(self, event: ClickableStatic.Clicked):
        event.stop()
        if 'like' in event.id:
            self.action_like()

        if 'repost' in event.id and not self.post.is_reposted:
            self.action_repost()


class OriginalPostWidget(PostWidget):
    def compose(self) -> ComposeResult:
        with Horizontal(classes='author'):
            yield Static(self.post.author.avatar, classes='author-avatar')
            with Vertical(classes='author-name'):
                with Horizontal(classes='author-display'):
                    yield Static(self.post.author.display_name, classes='subscribed' if self.post.author.is_subscribed else '')
                    if self.post.author.verified:
                        yield Static('', classes='verified')
                yield Static(f'@{self.post.author.username}', classes='author-username')
            with Horizontal(classes='actions'):
                yield Static('󰒗', classes='share')
                yield Static('', classes='copy')
                yield Static('', classes='report')

        yield Static(self.post.content)

        if self.post.attachments:
            yield ImageCarousel(self.post.attachments)


        with Horizontal(classes='stats'):
            yield ClickableStatic(f'{"" if self.post.is_liked else ""} {self.post.likes_count}', classes=f'likes{" active" if self.post.is_liked else ""}', id='original-like')
            yield ClickableStatic(f' {self.post.comments_count}', classes='comments', id='original-comment')
            yield ClickableStatic(f'󰑖 {self.post.reposts_count}', classes=f'reposts{" active" if self.post.is_liked else ""}', id='original-repost')
            yield ClickableStatic(f' {self.post.views_count}', classes=f'views{" active" if self.post.is_viewed else ""}', id='original-view')
