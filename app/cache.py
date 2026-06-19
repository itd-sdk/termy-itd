from io import BytesIO
from pathlib import Path

from itd.file import PostAttach
from requests import get

CACHE_DIR = Path(__file__).parent.parent / 'cache'
CACHE_DIR.mkdir(exist_ok=True)


def _get_path(attachment: PostAttach | str) -> Path:
    if isinstance(attachment, PostAttach):
        return CACHE_DIR / f'{attachment.id}.{attachment.extension}'
    return CACHE_DIR / attachment.split('images/')[-1]


def write(attachment: PostAttach | str) -> None:
    if isinstance(attachment, PostAttach):
        attachment.download(str(_get_path(attachment)))
    else:
        _get_path(attachment).write_bytes(get(attachment, timeout=30).content)


def read(attachment: PostAttach | str) -> bytes | None:
    path = _get_path(attachment)
    if path.exists():
        return path.read_bytes()


def get_and_maybe_write(attachment: PostAttach | str) -> BytesIO:
    data = read(attachment)

    if data is None:
        write(attachment)
        data = read(attachment)
        assert data

    buf = BytesIO(data)
    buf.seek(0)

    return buf
