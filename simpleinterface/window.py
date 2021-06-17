import abc
from collections.abc import Iterable
from .app import App
from .string_buffer import StringBuffer
# from .control import Button

class _Message:
    _type = ''

    def __init__(self, type):
        self._type = type

class Window:
    main_wnd = None
    handle = -1
    term = None

    debug = open('debug.log', 'w')

    def __init__(self):
        # self.term = Terminal()
        app = App()
        self.term = app.term
        self.background_clr = 'cyan'  # "magenta"
        self.text_clr = "white"

        app = App()
        self.screen = app.screen

    @abc.abstractmethod
    def set_base_corner(self, x=0, y=0): ...

    @abc.abstractmethod
    def set_right_corner(self, x, y): ...

    @abc.abstractmethod
    def set_parent(self, parent=None): ...

    @abc.abstractmethod
    def run(self, key=None) -> int: ...

    @abc.abstractmethod
    def render(self): ...

    @abc.abstractmethod
    def on_resize(self, sig, action): ...

    @abc.abstractmethod
    def on_paint(self): ...

    @abc.abstractmethod
    def on_focus(self, focus: bool = False): ...

    @abc.abstractmethod
    def add_main_menu(self, menu): ...

    def set_main_wnd(self, mainwnd):
        self.main_wnd = mainwnd

    @abc.abstractmethod
    def _focused_sub_wnd(self, handle, sub, focus=True) -> int: ...

    @abc.abstractmethod
    def child_lose_focus(self): ...

    @abc.abstractmethod
    def is_menu(self) -> bool: ...

    def set_handle(self, handle: int = -1):
        self.handle = handle

class MainWindow(Window):

    string_buffer = None

    def __init__(self):
        super().__init__()
        # self.term = Terminal()
        height, width = self.term.height, self.term.width

        self.left_top_corner = "\u250c"
        self.right_top_corner = "\u2510"
        self.left_bottom_corner = "\u2514"
        self.right_bottom_corner = "\u2518"
        self.hor_line = "\u2500"
        self.vert_line = "\u2502"
        self.background_clr = 'darkgrey' #'cyan'  # "magenta"
        self.main_menu = None
        self.main_menu_key = "KEY_F9"
        self.wnd_border = True
        self.work_spc_border = True
        self.focus_owner = True
        self.focus = True
        self.main_menu_focus = False
        self.selected_wnd = -1
        self.focused_wnd = None
        self.focused_wnd_handle = -1
        self.next_sub_wnd = ['KEY_TAB', 'KEY_RIGHT']
        self.prev_sub_wnd = ['KEY_LEFT']

        self.x = 0
        self.y = 0
        self.rx = width - 1
        self.ry = height - 1
        self.sub_windows = {}
        self.wnd_count = 0

        # self.string_buffer = ["",]
        # self.cur_pos = 0
        # self.delta = 0

        self.screen_id = self.screen.bind()
        self.main_wnd = self

        self.string_buffer = StringBuffer(self.text_clr, self.background_clr, self.screen, self.screen_id)
        self.work_size()



    def set_base_corner(self, x=0, y=0):
        ...

    def get_anchor(self)-> tuple:
        return (0, 0)

    def set_parent(self, parent=None):
        ...

    def shift_focus(self, direction='right'):

        handles = list(self.sub_windows.keys())
        handles.sort()

        if len(handles) != 0 and len(handles) > 1:

            pos:int = 0
            if direction == 'right':
                pos = handles.index(self.focused_wnd_handle) + 1
            elif direction == 'left':
                pos = handles.index(self.focused_wnd_handle) - 1

            if pos == len(handles):
                pos = 0

            if pos < 0:
                pos = len(handles) - 1

            self.focused_wnd.on_focus(False)
            # self.focused_wnd.on_paint()
            self.echo('handles = ' + str(handles) + ' pos = ' + str(pos) + '\n')
            self.focused_wnd = self.sub_windows[handles[pos]]
            self.focused_wnd.on_focus(True)
            self.focused_wnd_handle = handles[pos]
            # self.focused_wnd.on_paint()
            self.on_paint()

    def work_size(self):
        self.wl_x = self.x
        self.wl_y = self.y
        self.wr_x = self.rx
        self.wr_y = self.ry

        if self.wnd_border:
            self.wl_x = self.x + 1
            self.wl_y = self.y + 1
            self.wr_x = self.rx - 1
            self.wr_y = self.ry - 1

        if self.main_menu is not None:
            self.wl_y += 1

        w = (self.wr_x - self.wl_x)
        h = (self.wr_y - self.wl_y)
        self.string_buffer.set_work_size(self.wl_x, self.wl_y + 1, h, w)

    def echo(self, string=None):
        self.string_buffer.print(string)
        self.on_paint()

    def is_menu(self) -> bool:
        return False


    def attach(self, wnd=None):
        handle = self.wnd_count
        if wnd is not None:
            wnd.parent = self
            wnd.main_wnd = self #self.main_wnd
            wnd.handle = handle

            self.sub_windows[self.wnd_count] = wnd
            self.wnd_count += 1

    def _focused_sub_wnd(self, handle, sub, focus=True) -> int:
        # handle = self.wnd_count
        # if sub is not None:
        #     self.sub_windows[self.wnd_count] = sub
        #     self.wnd_count += 1

        if focus:
            if self.focused_wnd is not None and self.focused_wnd != sub:
                self.focused_wnd.on_focus(False)
            self.focused_wnd = sub
            self.main_menu_focus = False
            self.focus_owner = True
            if self.main_menu is not None:
                self.main_menu.on_focus(False)
            self.focused_wnd_handle = handle
            self.on_paint()

        return handle

    def _un_bind_window(self, handle=-1):
        handles = list(self.sub_windows.keys())
        handles.sort()
        pos = handles.index(handle)
        self.echo(f'un_bind 1 - {str(handles)}\n')

        try:
            self.sub_windows.pop(handle)
        except KeyError:
            print(f'Window handle \'{handle}\' does not exist')
            exit(-1)
        self.focused_wnd.on_focus(False)

        next_handle: int = 0
        handles.pop(pos)

        if len(handles) != 0:
            if len(handles) == 1:
                next_handle = handles[0]
            else:
                if pos >= len(handles):
                    next_handle = handles[0]
                else:
                    next_handle = handles[pos]
            self.echo('un bind 2 - ' + str(handles) + str(next_handle) + '\n')
            self.focused_wnd = self.sub_windows[next_handle]
            self.focused_wnd.on_focus(True)
            self.focused_wnd_handle = next_handle
        else:
            self.focused_wnd = None
        self.on_paint()

    def __clear_scr(self):
        height = self.ry - self.y
        width = self.rx - self.x
        scr_back_clr = getattr(self.term, 'on_' + self.background_clr)

        for x in range(width):
            for y in range(height):
                # echo(self.term.move_xy(x, y) + f'{scr_back_clr} ')
                self.screen.echo(self.screen_id, x, y, f'{scr_back_clr} {self.term.normal}{scr_back_clr}')

    def string_buffer_render(self):
        self.string_buffer.string_buffer_render()

    def get_string_buffer_symbol(self, x, y):
        return self.string_buffer.get_string_buffer_symbol(x, y)

    def window_render(self):
        height = self.ry - self.y
        width = self.rx - self.x
        scr_back_clr = getattr(self.term, 'on_' + self.background_clr)
        # print(self.term.clear())

        if self.wnd_border:
            # top corners
            self.screen.echo(self.screen_id, self.x, self.y, f'{scr_back_clr}{self.left_top_corner}{self.term.normal}{scr_back_clr}')
            self.screen.echo(self.screen_id, self.rx, self.y, f'{scr_back_clr}{self.right_top_corner}{self.term.normal}{scr_back_clr}')

            # bottom corners
            self.screen.echo(self.screen_id, self.x, self.ry, f'{scr_back_clr}{self.left_bottom_corner}{self.term.normal}{scr_back_clr}')
            self.screen.echo(self.screen_id, self.rx, self.ry, f'{scr_back_clr}{self.right_bottom_corner}{self.term.normal}{scr_back_clr}')

            # lines
            # horizontal lines
            for ii in range(0, width - 1, 1):
                self.screen.echo(self.screen_id, self.x + ii + 1, self.y, f'{scr_back_clr}{self.hor_line}{self.term.normal}{scr_back_clr}')
                self.screen.echo(self.screen_id, self.x + ii + 1, self.ry, f'{scr_back_clr}{self.hor_line}{self.term.normal}{scr_back_clr}')

            # vertical lines
            for ii in range(height - 1):
                self.screen.echo(self.screen_id, self.x, self.y + ii + 1, f'{scr_back_clr}{self.vert_line}{self.term.normal}{scr_back_clr}')
                self.screen.echo(self.screen_id, self.rx, self.y + ii + 1, f'{scr_back_clr}{self.vert_line}{self.term.normal}{scr_back_clr}')

        if self.work_spc_border:
            pass

        self.string_buffer_render()

        if self.main_menu is not None:
            self.main_menu.on_paint()

        for k, w in self.sub_windows.items():
            if k != self.focused_wnd_handle:
                w.on_paint()

        if self.focused_wnd is not None:
            self.focused_wnd.on_paint()


    def render(self):
        self.__clear_scr()
        self.window_render()


    def run(self, key=None):
        # clr = getattr(self.term, 'on_' + self.background_clr)
        # echo(f'{clr}')

        self.selection = 0

        # res = 0

        self.debug.write('main wnd ' + str(key) + f' {key.name}\n')

        if self.focused_wnd is not None and not self.main_menu_focus:
            key = self.focused_wnd.run(key)
        if key is not None and key.is_sequence:
            if key.name == self.main_menu_key: #and res != -1:
                self.focus_owner = not self.focus_owner
                self.main_menu.on_focus(not self.focus_owner)
                self.main_menu_focus = not self.focus_owner
                self.on_paint()
            else:
                if not self.focus_owner and self.main_menu_focus:
                    self.main_menu.run(key)
                else:
                    if key.name == 'KEY_ENTER':
                        return key
                    elif key.name in self.next_sub_wnd:
                        self.shift_focus(direction='right')
                        return None
                    elif key.name in self.prev_sub_wnd:
                        self.shift_focus(direction='left')
                        return None
                    else:
                        return key
                        # self.on_paint()
        return key

    def on_resize(self, sig, action):
        height, width = self.term.height, self.term.width
        self.rx = width - 1
        self.ry = height - 1
        self.work_size()
        self.screen.reset()
        self.on_paint()

    def on_paint(self):
        self.screen.begin()
        self.render()
        self.screen.end()

    def on_focus(self, focus: bool = False):
        pass

    def add_main_menu(self, menu):
        self.main_menu = menu
        self.main_menu.set_parent(self)
        self.main_menu.set_main_wnd(self)
        if self.wnd_border:
            self.main_menu.set_base_corner(1, 1)
        else:
            self.main_menu.set_base_corner(0, 0)


####################################################################################


class SubWindow(MainWindow):

    def __init__(self):
        super().__init__()
        self.parent = None
        self.wnd_border = True
        self.background_clr = "magenta"
        self.title = ""
        self.modal = False  # True
        self.escape = ["KEY_ESCAPE"] #, "KEY_LEFT"]
        self.handle = -1
        self.base_corner = None

        self.on_focus_dict = {'left_top_corner':'\u2554', 'right_top_corner':'\u2557',
                              'left_bottom_corner':'\u255A', 'right_bottom_corner':'\u255D',
                              'hor_line':'\u2550', 'vert_line':'\u2551'}

        self.not_focus_dict = {'left_top_corner':'\u250c', 'right_top_corner':'\u2510',
                               'left_bottom_corner':'\u2514', 'right_bottom_corner':'\u2518',
                               'hor_line':'\u2500', 'vert_line':'\u2502'}

        self.screen_id = self.screen.bind()
        self._display = False


    def set_base_corner(self, x=0, y=0):
        self.base_corner = (x, y)
        anchor = self.parent.get_anchor()
        self.x = 0
        self.y = 0
        self.screen.set_base_corner(self.screen_id, x + anchor[0], y + anchor[1])

    def get_anchor(self)-> tuple:
        anchor = (0, 0)
        if self.parent is not None:
            anchor = self.parent.get_anchor()
        return (self.base_corner[0] + anchor[0], self.base_corner[1] + anchor[1])

    def set_right_corner(self, x, y):
        self.rx = x - self.base_corner[0]
        self.ry = y - self.base_corner[1]
        self.work_size()

    def set_parent(self, parent=None):
        self.parent = parent

    def __clear_scr(self):
        height = self.ry - self.y
        width = self.rx - self.x
        clr = getattr(self.term, 'on_' + self.background_clr)
        for i in range(width):
            for j in range(height):
                self.screen.echo(self.screen_id, i, j, f'{clr} {self.term.normal}{clr}')

    def on_paint(self):
        self.screen.begin()
        self.render()
        self.screen.end()

    def __change_focus(self):
        if self.focus:
            self.left_top_corner = self.on_focus_dict['left_top_corner']
            self.right_top_corner = self.on_focus_dict['right_top_corner']
            self.left_bottom_corner = self.on_focus_dict['left_bottom_corner']
            self.right_bottom_corner = self.on_focus_dict['right_bottom_corner']
            self.hor_line = self.on_focus_dict['hor_line']
            self.vert_line = self.on_focus_dict['vert_line']
        else:
            self.left_top_corner = self.not_focus_dict['left_top_corner']
            self.right_top_corner = self.not_focus_dict['right_top_corner']
            self.left_bottom_corner = self.not_focus_dict['left_bottom_corner']
            self.right_bottom_corner = self.not_focus_dict['right_bottom_corner']
            self.hor_line = self.not_focus_dict['hor_line']
            self.vert_line = self.not_focus_dict['vert_line']

    def on_focus(self, focus: bool = False):
        self.focus = focus
        self.work_size()
        self.__change_focus()
        if self.focus and not self._display:
            self.main_wnd._focused_sub_wnd(self.handle, self, True)
            self._display = True

    def render(self):
        self.__clear_scr()
        self.window_render()
        if self.title != "":
            title = self.title
            clr = getattr(self.term, 'on_' + self.background_clr)
            title_length = len(self.title)
            width = self.rx - self.x
            pos = int((width - title_length) / 2.)
            self.screen.echo(self.screen_id, pos, 0, f'{clr}{title}{self.term.normal}{clr}')

    def __find_key(self, key, keys=None):
        if key is not None and isinstance(keys, Iterable):
            for k in keys:
                if k == keys:
                    return True
        return False

    def _remove_wnd(self):
        self.main_wnd._un_bind_window(self.handle)
        self.handle = -1
        self._display = False
        self.screen.disable_region(self.screen_id)

    def run(self, key=None):
        self.debug.write(f'1 {str(key.encode("unicode_escape"))} -- {key.is_sequence} -- {key.name}\n')
        if self.focused_wnd is not None and not self.main_menu_focus:
            key = self.focused_wnd.run(key)
        self.debug.write(f'2\n')
        if key is not None:
            if key.is_sequence:
                if key.name in self.escape:
                    self._remove_wnd()
                    self.debug.write(f'escape\n')
                    return None
                else:
                    return key
            # else:
            #     self.debug.write(f'3\n')
            #     self.echo(f'{key}')
        if self.modal:
            return None
        return key
    

