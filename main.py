import app.main

# from textual.app import App
# from textual.containers import Horizontal
# from textual.events import Click
# from textual.screen import Screen
# from textual.widgets import Static


# class TestStatic(Static):
#     def __init__(self):
#         super().__init__('test 123')

#     def on_click(self, event: Click):
#         self.log('static click')
#         event.stop()


# class TestWidget(Horizontal):
#     def compose(self):
#         yield TestStatic()

#     def on_click(self, event: Click):
#         self.log('widget click')
#         event.stop()


# class TestScreen(Screen):
#     def compose(self):
#         yield TestWidget()

#     def on_click(self, event: Click):
#         self.log('screen click')
#         event.stop()


# class TestApp(App):
#     def on_mount(self):
#         self.push_screen(TestScreen())


# TestApp().run()
