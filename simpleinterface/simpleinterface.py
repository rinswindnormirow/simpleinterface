#! /usr/bin/python3

import abc
import signal
import functools
import contextlib
from blessed import Terminal
from collections import namedtuple


echo = functools.partial(print, end='', flush=True)
# menuItem = namedtuple('menuItem', 'title enable sub_menu function')
class menuItem:
    def __init__(self, title:str="", enable: bool=True, sub_menu=None, function=None):
        self.title = title
        self.enable = enable
        self.sub_menu = sub_menu
        self.function = function

def singleton(cls):
    instance = None

    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)

        return instance
    return getinstance


@singleton
class Screen:
    screen = {(0, 0): "",}
    region = []
    change_region_cnt: int = 0

    def __init__(self):
        self.term = Terminal()

    def __render(self):
        screen2render = {}
        for region in self.region:
            for c, s in region.items():
                if c in self.screen.keys():
                    if s != self.screen[c]:
                        screen2render[c] = s
                else:
                    screen2render[c] = s

                self.screen[c] = s

        for c,s in screen2render.items():
            echo(self.term.move(c[1], c[0]) + s)

    def bind(self) -> int:
        self.region.append({})
        return len(self.region) - 1

    def begin(self):
        self.change_region_cnt += 1

    def end(self):
        self.change_region_cnt -= 1
        if self.change_region_cnt == 0:
            self.__render()
        if self.change_region_cnt < 0:
            print("хуйня")
            raise KeyError()

    def echo(self, region_id:int=-1, x=0, y=0, string=""):
        if region_id < 0 or region_id >= len(self.region):
            raise KeyError()
        c = (x, y)
        if c in self.region[region_id].keys():
            if string != self.region[region_id][c]:
                self.region[region_id][c] = string
        else:
            self.region[region_id][c] = string

@singleton
class App:
    def __init__(self):
        self.term = Terminal()
        self.mainwindow = None
        self.background_clr = 'cyan'  # "magenta"
        self.quit_keys = (u'q', u'Q')
        self.screen = Screen()

    def set_main_window(self, mainwindow=None):
        self.mainwindow = mainwindow

    def main_loop(self):

        clr = getattr(self.term, 'on_' + self.background_clr)
        echo(f'{clr}')

        if self.mainwindow is None:
            return

        # self.render()
        try:
            with self.term.fullscreen(), self.term.hidden_cursor():
                run = True
                self.mainwindow.on_paint()
                with self.term.cbreak():
                    while run:
                        key = self.term.inkey()
                        if self.quit_keys is not None and key in self.quit_keys:
                            run = False
                        else:
                            # if key.is_sequence:
                            self.mainwindow.run(key)
        except KeyboardInterrupt:
            pass
        clr = self.term.normal
        clr += self.term.clear
        echo(f'{clr}')


class Window:
    main_wnd = None
    handle = -1

    def __init__(self):
        self.term = Terminal()
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
    def bind_wnd(self, sub, focus=True) -> int: ...

    @abc.abstractmethod
    def child_lose_focus(self): ...

    @abc.abstractmethod
    def is_menu(self) -> bool: ...

    def set_handle(self, handle: int = -1):
        self.handle = handle


class MainMenu(Window):
    menu = None

    def __init__(self, name="main"):
        super().__init__()

        self.term = Terminal()
        self.screen_id = self.screen.bind()

        self.selection = 0
        self.left_top_corner = "\u250c"
        self.right_top_corner = "\u2510"
        self.left_bottom_corner = "\u2514"
        self.right_bottom_corner = "\u2518"
        self.hor_line = "\u2500"
        self.vert_line = "\u2502"

        self.next_select = ["KEY_TAB", "KEY_RIGHT"]
        self.prev_select = "KEY_LEFT"
        self.escape = ["KEY_ESCAPE"]

        self.background_clr = "magenta"
        self.cursor_back_clr = "bold_red_reverse"
        self.text_clr = "white"

        self.position = "top"
        self.gap = 6
        self.left_gap = 1
        self.focus_owner = False
        self.sub_menu_focus = False
        self.parent = None
        self.sub = None
        self.name = name

        self.width = self.term.width

        if self.position == "top":
            self.menu_x = 1
            self.menu_y = 1
        elif self.position == "bottom":
            self.menu_x = 1
            self.menu_y = self.term.height - 1

    def is_menu(self) -> bool:
        return True

    def set_handle(self, handle: int = -1):
        handle = -1

    def __make_menu_item(self, m_item):
        menu_name:str = m_item[0]
        menu_name = menu_name.replace(' ', '_')
        setattr(self, menu_name, menuItem(m_item[0], m_item[1], m_item[2], m_item[3]))

    def set_menu(self, menu: list = None):
        self.menu = menu
        if self.menu is not None:
            for m in self.menu:
                if m[2] is not None:
                    m[2].set_parent(self)
                    m[2].set_main_wnd(self.main_wnd)
                self.__make_menu_item(m)


    def set_base_corner(self, x=0, y=0):
        if self.position == "top":
            self.menu_x = x
            self.menu_y = y
        elif self.position == "bottom":
            self.menu_x = x
            self.menu_y = self.term.height - 1

    def set_parent(self, parent=None):
        self.parent = parent

    # def add_main_menu(self, menu):...

    def on_resize(self, sig, action):
        self.render()

    def on_paint(self):
        self.screen.begin()
        self.render()
        self.screen.end()

    def on_focus(self, focus: bool = False):
        self.focus_owner = focus
        if not focus:
            self.sub_menu_focus = False
            if self.sub is not None:
                self.sub.on_focus(False)

    def render(self):
        height, width = self.term.height, self.term.width
        scr_back_clr = getattr(self.term, 'on_' + self.background_clr)
        text_clr = getattr(self.term, self.text_clr)

        # with self.term.location(self.menu_x, self.menu_y):
        #     for ii in range(self.menu_x, width - self.menu_x, 1):
        #         echo(f'{scr_back_clr} ')

        for ii in range(self.menu_x, width - self.menu_x, 1):
            self.screen.echo(self.screen_id, self.menu_x + ii, self.menu_y, f'{scr_back_clr} ')

        # echo(self.term.normal)

        if self.menu is not None:
            echo(self.term.move(self.menu_y, self.menu_x))
            offset = self.left_gap
            for (idx, m) in enumerate(self.menu):
                title = m[0]
                if idx == self.selection and self.focus_owner:
                    clr = getattr(self.term, self.cursor_back_clr)
                else:
                    clr = scr_back_clr + text_clr

                # echo(self.term.move(self.menu_y, self.menu_x + offset) + f'{clr}{title}')

                self.screen.echo(self.screen_id, self.menu_x + offset, self.menu_y, f'{clr}{title}')

                # echo(self.term.normal)
                # echo(f'{scr_back_clr}')

                offset += len(title) + self.gap

        # echo(self.term.move(20, 10) + str(self.selection))

        if self.sub is not None and self.sub_menu_focus:
            self.sub.on_paint()

    def __sub(self):
        sel_name:str = self.menu[self.selection][0]
        sel_name = sel_name.replace(' ', '_')
        attr = getattr(self, sel_name)
        return attr

    def run_selection(self):
        sel = self.__sub()
        if sel.function is not None:
            sel.function()

    def sub_menu_base_corner(self):
        offset = 0
        for ii in range(self.selection):
            offset += len(self.menu[ii][0]) + self.gap
        self.sub.set_base_corner(self.menu_x + 2 + offset, self.menu_y + 1)

    def child_lose_focus(self):
        self.on_focus(True)
        self.sub_menu_focus = False
        self.main_wnd.on_paint()
        self.parent.on_paint()
        if self.sub is not None:
            self.sub.on_focus(False)

    def __remove_sub_focus(self):
        self.on_focus(True)
        self.sub_menu_focus = False
        self.parent.on_paint()
        if self.sub is not None:
            self.sub.on_focus(False)

    def run(self, key=None):
        self.on_paint()
        sub = self.__sub()
        self.sub = sub.sub_menu #self.menu[self.selection][2]
        if key is not None:
            if self.focus_owner and not self.sub_menu_focus:
                if key.name in self.next_select:
                    self.selection += 1
                elif key.name == self.prev_select:
                    self.selection -= 1
                elif key.name in self.escape:
                    self.parent.child_lose_focus()
                    return 0

                if not self.sub_menu_focus:
                    if key.name == 'KEY_ENTER':
                        if self.sub is not None:
                            self.sub_menu_focus = True
                            self.sub.set_main_wnd(self.main_wnd)
                            self.sub_menu_base_corner()
                            self.sub.on_focus(True)
                            self.sub.run()
                            return 0
                        else:
                            self.run_selection()
                            return 0
            else:
                if self.sub is not None:
                    self.sub.run(key)
                    return 0
        self.selection = self.selection % len(self.menu)
        self.on_paint()
        return 0


#############################################################################

class SubMenu(MainMenu):

    # menu = None
    # cnt = 4

    def __init__(self, name=""):
        super().__init__(name)
        self.term = Terminal()

        self.screen_id = self.screen.bind()

        self.wnd_border = False  # True
        self.background_clr = "magenta"
        self.cursor_back_clr = "bold_red_reverse"
        self.text_clr = "white"

        self.position = "top"

        self.selection = 0
        self.left_top_corner = "\u250c"
        self.right_top_corner = "\u2510"
        self.left_bottom_corner = "\u2514"
        self.right_bottom_corner = "\u2518"
        self.hor_line = "\u2500"
        self.vert_line = "\u2502"

        self.next_select = ["KEY_TAB", "KEY_DOWN"]
        self.prev_select = "KEY_UP"
        self.escape = ["KEY_ESCAPE", "KEY_LEFT"]

        self.focus_owner = False
        self.sub_menu_focus = False
        self.parent = None
        self.sub = None

        self.wnd_border = True

        self.menu_x = 1
        self.menu_y = 1
        self.__get_menu_size()

    def __get_menu_size(self):

        if self.menu is None:
            return

        self.m_height = len(self.menu) - 1
        self.m_max_len = 0
        for m in self.menu:
            self.m_max_len = len(m[0]) if self.m_max_len < len(m[0]) else self.m_max_len

        self.m_width = self.m_max_len

        if self.wnd_border:
            self.m_width += 2
            self.m_height += 2
            self.gap_x = self.menu_x + 1
            self.gap_y = self.menu_y + 1
            self.width = self.m_width - 2
            self.height = self.m_height - 2
        else:
            self.gap_x = self.menu_x
            self.gap_y = self.menu_y
            self.width = self.m_width
            self.height = self.m_height

    def is_menu(self) -> bool:
        return True

    def sub_menu_base_corner(self):
        if self.sub.is_menu():
            self.sub.set_base_corner(self.menu_x + self.m_width + 1, self.menu_y + self.selection + 1)

    def set_base_corner(self, x=0, y=0):
        self.menu_x = x
        self.menu_y = y
        self.__get_menu_size()

    def set_parent(self, parent=None):
        self.parent = parent

    def on_resize(self, sig, action):
        self.on_paint()

    # cnt = 0
    def on_paint(self):
        self.screen.begin()
        self.render()
        self.screen.end()

    def render(self):
        # height, width = self.term.height, self.term.width
        scr_back_clr = getattr(self.term, 'on_' + self.background_clr)
        text_clr = getattr(self.term, self.text_clr)

        # self.cnt += 1
        # echo(self.term.move(15, 10) + f'sub menu on_paint={self.cnt}')

        if self.wnd_border:
            # top corners
            with self.term.location(self.menu_x, self.menu_y):
                echo(f"{scr_back_clr}" + self.left_top_corner)

            with self.term.location(self.menu_x + self.m_width, self.menu_y):
                echo(f"{scr_back_clr}" + self.right_top_corner)

            # bottom corners
            with self.term.location(self.menu_x, self.menu_y + self.m_height):
                echo(f"{scr_back_clr}" + self.left_bottom_corner)

            with self.term.location(self.menu_x + self.m_width, self.menu_y + self.m_height):
                echo(f"{scr_back_clr}" + self.right_bottom_corner)

            # lines
            # horizontal lines
            for ii in range(0, self.m_width - 1, 1):
                with self.term.location(ii + self.menu_x + 1, self.menu_y):
                    echo(f"{scr_back_clr}" + self.hor_line)

                with self.term.location(ii + self.menu_x + 1, self.menu_y + self.m_height):
                    echo(f"{scr_back_clr}" + self.hor_line)

            # vertical lines
            for ii in range(self.m_height - 1):
                with self.term.location(self.menu_x, self.menu_y + ii + 1):
                    echo(f"{scr_back_clr}" + self.vert_line)

                with self.term.location(self.menu_x + self.m_width, self.menu_y + ii + 1):
                    echo(f"{scr_back_clr}" + self.vert_line)

        # echo(self.term.normal)
        w = self.m_max_len + 1

        echo(self.term.move(self.menu_y, self.menu_x))
        # offset = self.left_gap
        for (idx, m) in enumerate(self.menu):
            title = m[0]
            if idx == self.selection:
                clr = getattr(self.term, self.cursor_back_clr)
            else:
                clr = scr_back_clr + text_clr

            echo(self.term.move(self.gap_y + idx, self.gap_x) + f'{clr}{title:{w}}')
            echo(self.term.normal)
            echo(f'{scr_back_clr}')

        if self.sub is not None and self.sub_menu_focus:
            self.sub.on_paint()


###############################################################################

class MainWindow(Window):

    def __init__(self):
        super().__init__()
        self.term = Terminal()
        height, width = self.term.height, self.term.width

        self.left_top_corner = "\u250c"
        self.right_top_corner = "\u2510"
        self.left_bottom_corner = "\u2514"
        self.right_bottom_corner = "\u2518"
        self.hor_line = "\u2500"
        self.vert_line = "\u2502"
        self.background_clr = 'cyan'  # "magenta"
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

        self.work_size()

        self.string_buffer = ["",]
        self.cur_pos = 0
        self.delta = 0

        self.screen_id = self.screen.bind()


    def set_base_corner(self, x=0, y=0):
        ...

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

    def echo(self, string=None):
        w = (self.wr_x - self.wl_x)
        h  = (self.wr_y - self.wl_y)
        pos = self.cur_pos
        clr = getattr(self.term, 'on_' + self.background_clr)

        if self.main_menu is not None:
            self.delta = 1

        echo_str = self.string_buffer[pos]
        if str is not None:
            echo_str += string

            #подгоним строку под размер окна
            if len(echo_str) > w:
                echo_str = echo_str[len(echo_str) - w:]

            next_str = echo_str.find('\n')
            if next_str == -1:
                self.string_buffer[pos] = echo_str
                echo(self.term.move(self.wl_y + pos + self.delta, self.wl_x) + f'{clr}' + echo_str)
            else:

                if next_str == len(echo_str) - 1:
                    # /n стоит в конце строки
                    self.string_buffer[pos] = echo_str[:next_str]
                    self.string_buffer.append("")
                    echo(self.term.move(self.wl_y + pos + self.delta, self.wl_x) + f'{clr}' + echo_str[:next_str])
                else:
                    echo_str = string[:next_str]
                    echo(self.term.move(self.wl_y + pos + self.delta, self.wl_x) + f'{clr}' + echo_str)
                    self.string_buffer[pos] = echo_str

                    echo_str = string[next_str+1:]
                    echo(self.term.move(self.wl_y + pos + self.delta, self.wl_x) + f'{clr}' + echo_str)
                    self.string_buffer.append(echo_str)

                self.cur_pos += 1

            if self.cur_pos == h:
                self.string_buffer.pop(0)
                self.cur_pos -= 1


            # echo(self.term.move(self.wl_y + pos + self.delta, self.wl_x) + f'{clr}' + echo_str)

    def is_menu(self) -> bool:
        return False

    def bind_wnd(self, sub, focus=True) -> int:
        handle = self.wnd_count
        if sub is not None:
            self.sub_windows[self.wnd_count] = sub
            self.wnd_count += 1

        if focus:
            if self.focused_wnd is not None:
                self.focused_wnd.on_focus(False)
            self.focused_wnd = sub
            self.main_menu_focus = False
            self.focus_owner = True
            self.main_menu.on_focus(False)
            self.focused_wnd_handle = handle
            self.on_paint()

        return handle

    def un_bind_window(self, handle=-1):
        handles = list(self.sub_windows.keys())
        handles.sort()
        pos = handles.index(handle)
        self.echo(str(handles))

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
            self.echo(str(handles) + str(next_handle) + '\n')
            self.focused_wnd = self.sub_windows[next_handle]
            self.focused_wnd.on_focus(True)
            self.focused_wnd_handle = next_handle
        else:
            self.focused_wnd = None
        self.on_paint()

    def render(self):

        # height, width = self.term.height, self.term.width
        height = self.ry - self.y
        width = self.rx - self.x
        scr_back_clr = getattr(self.term, 'on_' + self.background_clr)
        echo(f'{scr_back_clr}')

        # print(self.term.clear())

        if self.wnd_border:
            # top corners
            with self.term.location(self.x, self.y):
                echo(f"{scr_back_clr}" + self.left_top_corner)

            with self.term.location(self.rx, self.y):
                echo(f"{scr_back_clr}" + self.right_top_corner)

            # bottom corners
            with self.term.location(self.x, self.ry):
                echo(f"{scr_back_clr}" + self.left_bottom_corner)

            with self.term.location(self.rx, self.ry):
                echo(f"{scr_back_clr}" + self.right_bottom_corner)

            # lines
            # horizontal lines
            for ii in range(0, width - 1, 1):
                with self.term.location(self.x + ii + 1, self.y):
                    echo(f"{scr_back_clr}" + self.hor_line)

                with self.term.location(self.x + ii + 1, self.ry):
                    echo(f"{scr_back_clr}" + self.hor_line)

            # vertical lines
            for ii in range(height - 1):
                with self.term.location(self.x, self.y + ii + 1):
                    echo(f"{scr_back_clr}" + self.vert_line)

                with self.term.location(self.rx, self.y + ii + 1):
                    echo(f"{scr_back_clr}" + self.vert_line)
        if self.work_spc_border:
            pass

        pos = 0
        for s in self.string_buffer:
            echo(self.term.move(self.wl_y + pos + self.delta, self.wl_x) + f'{scr_back_clr}' + s)
            pos += 1

        if self.main_menu is not None:
            self.main_menu.on_paint()

        for k, w in self.sub_windows.items():
            if k != self.focused_wnd_handle:
                w.on_paint()

        if self.focused_wnd is not None:
            self.focused_wnd.on_paint()

        echo(f'{scr_back_clr}')

    def run(self, key=None):
        clr = getattr(self.term, 'on_' + self.background_clr)
        echo(f'{clr}')

        self.selection = 0

        # res = 0

        if self.focused_wnd is not None and not self.main_menu_focus:
            self.focused_wnd.run(key)
        if key.is_sequence:
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
                        pass
                    elif key.name in self.next_sub_wnd:
                        self.shift_focus(direction='right')
                    elif key.name in self.prev_sub_wnd:
                        self.shift_focus(direction='left')
                    else:
                        self.on_paint()
        return 0

    def on_resize(self, sig, action):
        height, width = self.term.height, self.term.width
        self.rx = width - 1
        self.ry = height - 1
        self.on_paint()

    def on_paint(self):
        self.screen.begin()
        clr = getattr(self.term, 'on_' + self.background_clr)
        echo(f'{clr}')
        print(self.term.clear())
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

        self.on_focus_dict = {'left_top_corner':'\u2554', 'right_top_corner':'\u2557',
                              'left_bottom_corner':'\u255A', 'right_bottom_corner':'\u255D',
                              'hor_line':'\u2550', 'vert_line':'\u2551'}

        self.not_focus_dict = {'left_top_corner':'\u250c', 'right_top_corner':'\u2510',
                              'left_bottom_corner':'\u2514', 'right_bottom_corner':'\u2518',
                              'hor_line':'\u2500', 'vert_line':'\u2502'}

        self.screen_id = self.screen.bind()

    def set_base_corner(self, x=0, y=0):
        self.x = x
        self.y = y

    def set_right_corner(self, x, y):
        self.rx = x
        self.ry = y

    def set_parent(self, parent=None):
        self.parent = parent

    def __clear_scr(self):
        height = self.ry - self.y
        width = self.rx - self.x
        clr = getattr(self.term, 'on_' + self.background_clr)
        for i in range(width):
            for j in range(height):
                echo(self.term.move(self.y + j, self.x + i) + f'{clr} ')

    def on_paint(self):
        self.screen.begin()
        clr = getattr(self.term, 'on_' + self.background_clr)
        echo(f'{clr}')
        self.__clear_scr()
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
        if self.focus:
            self.on_paint()
            if self.handle == -1:
                self.handle = self.main_wnd.bind_wnd(self, True)
                self.parent = self.main_wnd

    def render(self):
        super().render()
        if self.title != "":
            title = self.title
            clr = getattr(self.term, 'on_' + self.background_clr)
            title_length = len(self.title)
            width = self.rx - self.x
            pos = int((width - title_length) / 2.)
            echo(self.term.move(self.y, self.x + pos) + f'{clr}{title}')

    def run(self, key=None):
        if key is not None:
            # echo(self.term.move(self.y + 1, self.y + 1) + f'{key}')
            if key.is_sequence:
                if key.name == self.main_wnd.main_menu_key and self.modal:
                    return -1
                if key.name in self.escape:
                    self.main_wnd.un_bind_window(self.handle)
                    self.handle = -1
            else:
                self.echo(f'{key}')
        return 0


class Control(SubWindow):

    def __init__(self):
        super().__init__()

class Edit(Control):
    def __init__(self):
        super(Edit, self).__init__()
        self.screen_id = self.screen.bind()


if __name__ == '__main__':

    main_wnd = MainWindow()
    app = App()
    app.set_main_window(main_wnd)
    app.quit_keys = None

    left = [15, 15]
    right = [60, 20]

    def create_window():
        app = App()
        # print(app)
        sub_wnd = SubWindow()
        sub_wnd.title = "sub window"
        sub_wnd.set_base_corner(*left)
        sub_wnd.set_right_corner(*right)
        sub_wnd.modal = False
        sub_wnd.set_main_wnd(app.mainwindow)
        # print(left, right)
        sub_wnd.on_focus(True)
        offset = int((right[0] - left[0])/ 2)
        left[0] += offset
        left[1] += 2
        right[0] += offset
        right[1] += 2
        # sub_wnd.run()

    sub_wnd = SubWindow()
    sub_wnd.title = "sub window"
    sub_wnd.set_base_corner(15, 15)
    sub_wnd.set_right_corner(60, 20)
    sub_wnd.modal = True

    sub_sub_sub_menu_2 = SubMenu("sub_sub_sub_menu_2")
    sub_sub_sub_menu_2.set_menu(
        [["При пожаре", True, None, None],
         ["Воруй", True, None, None],
         ["Убивай", True, None, None],
         ["Еби гусей", True, None, None],
         ["Жди ответного гудка", True, None, None]])

    sub_sub_sub_menu_1 = SubMenu("sub_sub_sub_menu_1")
    sub_sub_sub_menu_1.set_menu([
        ["Хуй", True, None, None],
        ["Пизда", True, None, None],
        ["Джигурда", True, sub_sub_sub_menu_2, None]])

    sub_sub_sub_menu = SubMenu("sub_sub_sub_menu")
    sub_sub_sub_menu.set_menu([
        ["Жопа", True, None, None],
        ["Кеды", True, None, None],
        ["Примус", True, sub_sub_sub_menu_1, None],
        ["Керосин", True, None, None]])

    sub_sub_menu = SubMenu("sub_sub_menu")
    sub_sub_menu.set_menu([
        ["Жопа", True, None, None],
        ["Кеды", True, None, None],
        ["Примус", True, None, None],
        ["Керосин", True, None, None]])

    sub_sub_menu_1 = SubMenu("sub_sub_menu_1")
    sub_sub_menu_1.set_menu([
        ["Жопа", True, None, None],
        ["Кеды", True, None, None],
        ["Примус", True, None, None],
        ["Керосин", True, None, None]])

    sub_sub_menu_2 = SubMenu("sub_sub_menu_2")
    sub_sub_menu_2.set_menu([
        ["Три", True, None, None],
        ["мандаблядское", True, None, None],
        ["пиздапроебище", True, None, None],
        ["в своем", True, sub_sub_sub_menu, None],
        ["злоебучем", True, None, None],
        ["троепиздии", True, None, None]])

    first_sub = SubMenu("first_sub")
    first_sub.set_menu([
        ["туда", True, None, None],
        ["сюда", True, sub_sub_menu, None],
        ["отсюда", True, None, None],
        ["exit", True, None, None]])

    # first_sub.exit._replace(function=exit)
    first_sub.exit.function = exit

    second_sub = SubMenu("second_sub")
    second_sub.set_menu([
        ["куда", True, None, None],
        ["идём", True, None, None],
        ["мы с пятачком", True, sub_sub_menu_1, None],
        ["большой", True, None, None],
        ["большой", True, None, None],
        ["секрет", True, sub_sub_menu_2, None]])

    second_sub.идём.function = create_window

    third_sub = SubMenu("third_sub")
    third_sub.set_menu([
        ["растуды", True, None, None],
        ["твою", True, None, None],
        ["в качель", True, None,None],
        ["реж", True, None,None],
        ["последний", True, None,None],
        ["огурец", True, None,None]])

    menu = MainMenu("main")
    menu.set_menu([
        ["login to system", True, first_sub, None],
        ["create account", True, second_sub, None],
        ["disconnect", True, third_sub, None]])

    main_wnd.add_main_menu(menu)
    signal.signal(signal.SIGWINCH, main_wnd.on_resize)

    app.main_loop()
