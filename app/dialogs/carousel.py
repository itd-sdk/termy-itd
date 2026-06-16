from itd.enums import AttachType
from itd.file import CommentAttach, PostAttach
from PIL import Image, UnidentifiedImageError
from textual.app import ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Static
from textual_image.widget import SixelImage
from textual_imageview.viewer import ImageViewer

from app.cache import get_and_maybe_write


class CarouselDialog(ModalScreen):
    BINDINGS = [
        Binding('escape', 'dismiss', 'Закрыть'),
        Binding('left', 'previous', 'Предыдущее вложение'),
        Binding('right', 'next', 'Следующее вложение'),
        Binding('s', 'toggle_sixel', 'Высокая графика')
    ]
    CSS_PATH = '../css/carousel.tcss'
    idx: reactive[int] = reactive(0, recompose=True)
    is_sixel: reactive[bool] = reactive(True, recompose=True)

    def __init__(self, attachments: list[PostAttach] | list[CommentAttach], idx: int = 0) -> None:
        super().__init__()
        self.attachments = attachments
        self.idx = idx
        self.empty = not bool(attachments)
        if self.empty:
            return

        self.files = []
        for attachment in attachments:
            if attachment.type == AttachType.IMAGE:
                # хотя в инлайн карусели итак есть провекра на ломаные вложения, тут еще раз проверяется чтоб не была ошибка если вложений несколько и полмоано только одно из них (и потом можно просто стрелками до нее долистать)
                # TODO: вообще лучше проверять ток 1 раз
                try:
                    img = Image.open(get_and_maybe_write(attachment))
                    img.copy().verify()
                except UnidentifiedImageError, OSError:
                    self.files.append('Не удалось открыть вложение')
                else:
                    self.files.append(img)
            else:
                self.files.append(None)

    def action_next(self):
        if self.idx < len(self.attachments) - 1:
            self.idx += 1

    def action_previous(self):
        if self.idx > 0:
            self.idx -= 1

    def action_toggle_sixel(self):
        self.is_sixel = not self.is_sixel

    def compose(self) -> ComposeResult:
        if self.empty:
            yield Static('Нет вложений (погоди ты как это открыл)', classes='attach-error')
        elif self.attachment.type == AttachType.IMAGE:
            assert self.file
            if isinstance(self.file, str):
                yield Static(self.file, classes='attach-error')
            elif self.is_sixel:
                yield SixelImage(self.file, classes='sixel')
            else:
                yield ImageViewer(self.file)

        elif self.attachment.type == AttachType.VIDEO:
            yield Static('[VIDEO]', classes='attachment')

        elif self.attachment.type == AttachType.AUDIO:
            yield Static('[AUDIO]', classes='attachment')

        else:
            yield Static('[MEDIA]', classes='attachment')

        yield Static(f'{self.idx + 1}/{len(self.attachments)}', id='idx')

    @property
    def attachment(self):
        return self.attachments[self.idx]

    @property
    def file(self):
        return self.files[self.idx]
