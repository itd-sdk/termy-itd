from typing import Iterable

from itd import User
from itd.enums import AttachType
from itd.file import CommentAttach, PostAttach
from pygments.console import esc
from rich.markup import escape
from textual import work
from textual.app import ComposeResult
from textual.containers import HorizontalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static
from textual_image.renderable.halfcell import Image as HalfcellRenderable
from textual_image.widget import HalfcellImage

from app.cache import get_and_maybe_write
from app.dialogs import CarouselDialog


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
                    self.classes = ' '.join(classes)
            else:
                self.classes = classes

    def __init__(self, content: str = '', *, id: str | None = None, classes: str | None = None, markup: bool = True) -> None:
        super().__init__(content, id=id, classes=classes, markup=markup)

    def on_click(self):
        if self.classes:
            self.post_message(self.Clicked(self.classes))


class Image(HalfcellImage, Renderable=HalfcellRenderable):
    class Clicked(Message):
        def __init__(self, idx: int) -> None:
            super().__init__()
            self.idx = idx

    def __init__(self, image: PostAttach, idx: int) -> None:
        super().__init__(classes='image', on_error=lambda e: Static(f'Ошибка: {e}', classes='error'))
        self.attachment = image
        self.loading = True
        self.idx = idx

    @work(thread=True)
    def load_image(self):
        self.image = get_and_maybe_write(self.attachment)

        def _remove_loading():
            self.loading = False

        self.call_next(_remove_loading)

    def on_mount(self):
        self.load_image()

    def on_click(self):
        self.post_message(self.Clicked(self.idx))


class ImageCarousel(HorizontalScroll):
    failed_ids: reactive[list[int]] = reactive([], recompose=True)

    def __init__(self, attachments: list[PostAttach] | list[CommentAttach]) -> None:
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


class Avatar(ClickableStatic):
    def __init__(self, avatar: str, *, classes: str | None = None):
        super().__init__(avatar, classes=classes)
        self.add_class('avatar')

    def on_click(self):
        self.notify('todo')


class DisplayName(ClickableStatic):
    def __init__(self, user: User, *, classes: str | None = None):
        content = '[bold underline]' + escape(user.display_name) + '[/bold underline]'
        if user.is_subscribed:
            content = '[#4fc3f7]' + content + '[/#4fc3f7]'
        if user.verified:
            content += ' [#0080ff][/#0080ff]'

        super().__init__(content, classes=classes)

    def on_click(self):
        self.notify('todo')
