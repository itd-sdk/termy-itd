from io import BytesIO

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import HorizontalScroll
from textual_image.widget import SixelImage, SixelOptions
from itd import Post
from itd.enums import AttachType
from requests import get


class PostWidget(Widget):
    def __init__(self, post: Post):
        super().__init__(classes='post')
        self.post = post

    def compose(self) -> ComposeResult:
        yield Static(self.post.content)
        if self.post.attachments:
            yield HorizontalScroll(
                *(SixelImage(BytesIO(get(attachment.url).content), classes='post-image', sixel_options=SixelOptions(64, False, 'maxcoverage')) for attachment in self.post.attachments if attachment.type == AttachType.IMAGE)
            )