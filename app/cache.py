from pathlib import Path
from io import BytesIO

from itd.file import PostAttach

CACHE_DIR = Path(__file__).parent.parent / 'cache'
CACHE_DIR.mkdir(exist_ok=True)

def _get_path(attachment: PostAttach) -> Path:
    return CACHE_DIR / f'{attachment.id}.{attachment.extension}'

def write(attachment: PostAttach) -> None:
    attachment.download(str(_get_path(attachment)))

def read(attachment: PostAttach) -> bytes | None:
    path = _get_path(attachment)
    if path.exists():
        return path.read_bytes()

def get_and_maybe_write(attachment: PostAttach) -> BytesIO:
    data = read(attachment)

    if data is None:
        write(attachment)
        data = read(attachment)
        assert data

    buf = BytesIO(data)
    buf.seek(0)
    return buf
