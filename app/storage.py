from json import dump, load
from pathlib import Path

path = Path("storage.json")
if path.exists():
    storage: dict = load(path.open())
else:
    storage = {}
    path.write_text("{}")


def flush():
    global storage

    with path.open("w") as fl:
        dump(storage, fl)
