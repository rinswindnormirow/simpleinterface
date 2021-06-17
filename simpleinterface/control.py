from .window import SubWindow, _Message
from .string_buffer import StringBuffer

import traceback

class Control(SubWindow):

    def __init__(self):
        super().__init__()

    def run(self, key=None):
        return key

    def set_base_corner(self, x=0, y=0):
        self.base_corner = (x, y)
        anchor = self.parent.get_anchor()
        self.x = 0
        self.y = 0
        self.screen.set_base_corner(self.screen_id, x + anchor[0], y + anchor[1])

    def get_size(self) -> tuple:
        ...


class Button(Control):
    caption = ""
    on_enter = None

    def __init__(self, caption=''):
        super(Button, self).__init__()
        self.select_background_clr = 'red'
        self.background_clr = 'olive'
        self.selection = True
        self.caption = caption
        self.x = 0
        self.y = 0
        self.rx = 0
        self.ry = 0

    def set_base_corner(self, x=0, y=0):
        super(Button, self).set_base_corner(x, y)
        # self.rx = len(self.caption) + 6 - self.base_corner[0]
        # self.ry = 1 - self.base_corner[1]

    def get_size(self) -> tuple:
        self.work_size()
        return (len(self.caption) + 2, 1)

    def work_size(self):
        self.wl_x = self.x
        self.wl_y = self.y
        self.wr_x = self.x + len(self.caption) + 2
        self.wr_y = self.y + 1

        w = (self.wr_x - self.wl_x)
        h = (self.wr_y - self.wl_y)
        self.string_buffer.set_work_size(self.wl_x, self.wl_y, h, w)

    def set_right_corner(self, x, y):
        ...

    def __clear_scr(self):
        height = self.ry - self.y
        width = self.rx - self.x
        if self.selection:
            clr = getattr(self.term, 'on_' + self.select_background_clr)
        else:
            clr = getattr(self.term, 'on_' + self.background_clr)

        for i in range(width):
            for j in range(height):
                self.screen.echo(self.screen_id, i, j, f'{clr} {self.term.normal}{clr}')

    def on_focus(self, focus: bool = False):
        self.selection = focus
        self.on_paint()

    def render(self):
        if self.selection:
            clr = getattr(self.term, 'on_' + self.select_background_clr)
        else:
            clr = getattr(self.term, 'on_' + self.background_clr)
        self.__clear_scr()
        self.screen.echo(self.screen_id, 1, 0, f'{clr}[{self.caption}]{self.term.normal}{clr}')

    def run(self, key=None):
        key = super(Button, self).run(key)
        if key is not None and key.is_sequence:
            if key.name == 'KEY_ENTER':
                if self.on_enter is not None and callable(self.on_enter):
                    self.on_enter()
                return None
        return key

class Edit(Control):
    caption = ""
    size = 0
    __begin = 0
    __end = 0
    # __string_buffer = None

    def __init__(self, caption=''):
        super(Edit, self).__init__()
        self.screen_id = self.screen.bind()
        self.edit_field_clr = 'darkgrey'
        self.background_clr = self.edit_field_clr
        self.caption_bck_clr = "magenta"
        self.__cursor_pos = 0
        self.string_buffer = StringBuffer(self.text_clr, self.background_clr, self.screen, self.screen_id)
        self.caption = caption

    def text(self):
        return self.string_buffer.get_string(0)

    def get_size(self) -> tuple:
        return (self.rx, self.ry)

    def render(self):
        caption_bck_clr = getattr(self.term, 'on_' + self.caption_bck_clr)
        edit_field_bck_clr = getattr(self.term, 'on_' + self.edit_field_clr)

        cursor_color = f'bold_{self.text_clr}_reverse'
        cursor_clr = getattr(self.term, cursor_color)
        blinking_mode = "\x1b[5m"

        if not self.focus:
            cursor_clr = u''
            blinking_mode = u''

        self.screen.echo(self.screen_id, self.x, self.y, f'{caption_bck_clr}{self.caption}{self.term.normal}{caption_bck_clr}')
        for ii in range(self.size):
            self.screen.echo(self.screen_id,
                             self.x + len(self.caption) + ii,
                             self.y,
                             f'{edit_field_bck_clr} {self.term.normal}{caption_bck_clr}')

        self.string_buffer.string_buffer_render(self.__begin, self.__end)

        symbol = self.get_string_buffer_symbol(self.__begin + self.__cursor_pos, 0)

        if symbol == u'':
            self.debug.write(f'Edit: {self.focus}\n')
            if self.focus:
                symbol = '\u2588'
            else:
                symbol = '\u2395'

        self.screen.echo(self.screen_id,
                         self.x + len(self.caption) + self.__cursor_pos,
                         self.y,
                         f'{edit_field_bck_clr}{cursor_clr}{blinking_mode}{symbol}{self.term.normal}{edit_field_bck_clr}')


    def on_paint(self):
        self.screen.begin()
        # self.work_size()
        self.render()
        self.screen.end()

    def on_focus(self, focus: bool = False):
        trace = traceback.extract_stack()
        self.debug.write(f'Edit: on_focus = {focus}\n')
        self.debug.write(f'Edit = {trace}\n')
        self.focus = focus
        self.work_size()
        if self.focus:
            self.main_wnd._focused_sub_wnd(self.handle, self, True)
            self.parent = self.main_wnd

    def work_size(self):
        self.wl_x = self.x + len(self.caption)
        self.wl_y = self.y
        self.wr_x = self.x + len(self.caption) + self.size
        self.wr_y = self.y + 1

        w = (self.wr_x - self.wl_x)
        h = (self.wr_y - self.wl_y)
        self.string_buffer.set_work_size(self.wl_x, self.wl_y, h, w)

    def run(self, key=None):
        # self.work_size()
        # self.debug.write(f'edit 1 - {key}\n')
        if not key.is_sequence:
            self.string_buffer.print(key, self.__begin + self.__cursor_pos)

            if self.string_buffer.get_string_len(0) < self.size:
                # строка не заполнена
                self.__end += 1
                self.__cursor_pos += 1
            else:
                if self.__cursor_pos == self.size - 1:
                    # курсор находится в крайней правой позиции
                    self.__end += 1
                    self.__begin += 1
                else:
                    self.__cursor_pos += 1

            self.on_paint()
            # self.debug.write(f'edit 2 - {key}\n')
            return None
        else:
            if key.name == 'KEY_BACKSPACE':
                if self.__cursor_pos > 0:
                    self.string_buffer.remove_ch(self.__begin + self.__cursor_pos - 1)
                    self.__cursor_pos -= 1
                    if self.string_buffer.get_string_len(0) < self.size:
                        if self.__end > 0:
                            self.__end -= 1
                self.on_paint()
                return None
            if key.name == 'KEY_DELETE':
                # if self.__cursor_pos > 0:
                self.string_buffer.remove_ch(self.__begin + self.__cursor_pos)
                # self.__cursor_pos -= 1
                if self.string_buffer.get_string_len(0) < self.size:
                    if self.__end > 0:
                        self.__end -= 1
                self.on_paint()
                return None
            if key.name == 'KEY_LEFT':
                if self.__cursor_pos > 0:
                    self.__cursor_pos -= 1
                else:
                    if self.__begin > 0:
                        self.__begin -= 1
                        self.__end -= 1
                self.on_paint()
                return None
            if key.name == 'KEY_RIGHT':
                if self.__cursor_pos < self.size - 1:
                    if self.string_buffer.get_string_len(0) > self.__cursor_pos:
                        self.__cursor_pos += 1
                else:
                    if self.__end <= self.string_buffer.get_string_len(0):
                        self.__begin += 1
                        self.__end += 1
                self.on_paint()
                return None
        return key