from io import BytesIO

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import HorizontalScroll, Horizontal, Vertical
from textual_image.widget import HalfcellImage
from itd import Post
from itd.enums import AttachType
from requests import get

from app.dialogs import RepostDialog


class _ClickableStatic(Static):
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
    def __init__(self, post: Post):
        super().__init__(classes='post')
        self.post = post

    def compose(self) -> ComposeResult:
        with Horizontal(classes='post-author'):
            yield Static(self.post.author.avatar, classes='post-author-avatar')
            with Vertical(classes='post-author-name'):
                yield Static(self.post.author.display_name)
                yield Static(f'@{self.post.author.username}', classes='post-author-username')
            with Horizontal(classes='post-actions'):
                yield Static('󰒗', classes='post-share')
                yield Static('', classes='post-copy')
                yield Static('', classes='post-report')

        yield Static(self.post.content)

        if self.post.attachments:
            with HorizontalScroll(classes='post-images'):
                for attachment in self.post.attachments:
                    if attachment.type != AttachType.IMAGE:
                        continue

                    yield HalfcellImage(BytesIO(get(attachment.url).content), classes='post-image')

        with Horizontal(classes='post-stats'):
            yield _ClickableStatic(f'{"" if self.post.is_liked else ""} {self.post.likes_count}', classes=f'post-likes{" active" if self.post.is_liked else ""}', id='like')
            yield _ClickableStatic(f' {self.post.comments_count}', classes='post-comments', id='comment')
            yield _ClickableStatic(f'󰑖 {self.post.reposts_count}', classes=f'post-reposts{" active" if self.post.is_liked else ""}', id='repost')
            yield _ClickableStatic(f' {self.post.views_count}', classes=f'post-views{" active" if self.post.is_viewed else ""}', id='view')


    def on__clickable_static_clicked(self, event: _ClickableStatic.Clicked):
        if event.id == 'like':
            button = self.query_one('.post-likes', _ClickableStatic)

            if self.post.is_liked:
                button.remove_class('active')
                self.post.unlike()
                button.update(f' {self.post.likes_count}')
            else:
                button.add_class('active')
                self.post.like()
                button.update(f' {self.post.likes_count}')

        if event.id == 'repost' and not self.post.is_reposted:
            def repost(text: str | None = None):
                if text is None:
                    return

                button = self.query_one('.post-reposts', _ClickableStatic)
                button.add_class('active')
                self.post.repost(text)
                button.update(f'󰑖 {self.post.reposts_count}')

            self.app.push_screen(RepostDialog(), repost)
