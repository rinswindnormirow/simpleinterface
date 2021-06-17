from blessed import Terminal

from .common import singleton
from .screen import Screen
from .common import echo

@singleton
class App:
    def __init__(self):
        self.term = Terminal(force_styling=True)
        self.mainwindow = None
        self.background_clr = 'cyan'  # "magenta"
        self.quit_keys = (u'q', u'Q')
        self.screen = Screen()
        self.run = True

    def set_main_window(self, mainwindow=None):
        self.mainwindow = mainwindow

    def main_loop(self):

        clr = getattr(self.term, 'on_' + self.background_clr)
        echo(f'{clr}')

        if self.mainwindow is None:
            return
        try:
            with self.term.fullscreen(), self.term.hidden_cursor(), self.term.raw():
                self.run = True
                self.mainwindow.on_paint()
                with self.term.cbreak():
                    while self.run:
                        key = self.term.inkey()
                        if self.quit_keys is not None and (key in self.quit_keys or key == chr(3)):
                            self.run = False
                        else:
                            self.mainwindow.run(key)
        except KeyboardInterrupt:
            pass
        clr = self.term.normal
        clr += self.term.clear
        echo(f'{clr}')

    def exit(self, kode=1):
        self.run = False