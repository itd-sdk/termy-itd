from typing import cast

from qrcode.main import QRCode
from textual.widget import Widget


class QRWidget(Widget):
    def __init__(self, data: str | None = None):
        super().__init__()
        self.qr = QRCode()
        if data:
            self.set_data(data)

    def set_data(self, data: str):
        self.qr.add_data(data, optimize=50)
        self.qr.make()
        self.styles.height = (self.qr.modules_count + 4) // 2
        self.styles.width = self.qr.modules_count + 4
        self.log(self.styles.height, self.styles.width)
        self.log(self.qr.data_list)
        self.refresh(recompose=True, layout=True)

    def render(self):
        if not self.qr.data_list:
            return 'no data'
        result = ''

        # source: qrcode lib
        modcount = self.qr.modules_count
        codes = [bytes((code,)).decode('cp437') for code in (255, 223, 220, 219)]

        def get_module(x, y) -> int:
            if min(x, y) < 0 or max(x, y) >= modcount:
                return 0
            return cast(int, self.qr.modules[x][y])

        for r in range(-2, modcount + 2, 2):
            for c in range(-2, modcount + 2):
                pos = get_module(r, c) + (get_module(r + 1, c) << 1)
                result += codes[pos]
            result += '\n'

        return result
