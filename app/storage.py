from json import dump, load

PATH = 'storage.json'

with open(PATH, 'r') as fl:
    storage: dict = load(fl)

def flush():
    global storage

    with open(PATH, 'w') as fl:
        dump(storage, fl)