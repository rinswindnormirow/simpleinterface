from .window import SubWindow
from .control import Button
from .string_buffer import StringBuffer


class DialogForm(SubWindow):

    def __init__(self, title=None):
        super(DialogForm, self).__init__()

        self.ok_button = Button("OK")
        self.cancel_button = Button("CANCEL")

        self.next_sub_wnd = ['KEY_TAB',]
        self.attach(self.ok_button)
        self.attach(self.cancel_button)

        self.ok_button.on_enter = self.on_ok
        self.cancel_button.on_enter = self.on_cancel

        if title is not None:
            self.title = title

        self.string_buffer = StringBuffer(self.text_clr, self.background_clr, self.screen, self.screen_id)


    def set_right_corner(self, x, y):
        super(DialogForm, self).set_right_corner(x, y)
        h = self.wr_y - self.wl_y
        w = self.wr_x - self.wl_x
        ok_size = self.ok_button.get_size()
        cancel_size = self.cancel_button.get_size()

        blk_size_x = ok_size[0] + cancel_size[0] + 2
        self.ok_button.set_base_corner(self.wl_x + (w - blk_size_x), self.wr_y)
        self.cancel_button.set_base_corner(self.wl_x  + (w - blk_size_x + ok_size[0] + 1), self.wr_y)

        # self.debug.write(f'blk = {blk_size_x}, ok_size = {ok_size}, {w}, {h}, {self.wl_x}\n')

        self.ok_button.on_focus(True)
        self.cancel_button.on_focus(False)

    def on_ok(self):
        self.echo('on_ok\n')

    def on_cancel(self):
        self.echo('on_cancel\n')
        self._remove_wnd()

    def run(self, key=None):
        key = super(DialogForm, self).run(key)
        if key is not None:
            if key.is_sequence:
                if key.name in self.next_sub_wnd:
                    self.shift_focus(direction='right')
                    return None
                if key.name == 'KEY_ENTER':
                    self.on_ok()
                    return None
        return key