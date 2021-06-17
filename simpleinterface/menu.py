from .common import menuItem, echo, singleton
from .window import  Window

class MainMenu(Window):
    menu = None

    def __init__(self, name="main"):
        super().__init__()

        # self.term = Terminal()
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
        self.disabled_pos_clr = 'ivory4_reverse'
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
            self.menu_y = self.term.__height - 1

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
                self.sub.on_paint()

    def render(self):
        height, width = self.term.height, self.term.width
        scr_back_clr = getattr(self.term, 'on_' + self.background_clr)
        text_clr = getattr(self.term, self.text_clr)
        disabled_clr = getattr(self.term, self.disabled_pos_clr)

        # with self.term.location(self.menu_x, self.menu_y):
        #     for ii in range(self.menu_x, width - self.menu_x, 1):
        #         echo(f'{scr_back_clr} ')

        for ii in range(width - self.menu_x - 1):
            self.screen.echo(self.screen_id, self.menu_x + ii, self.menu_y, f'{scr_back_clr} {self.term.normal}{scr_back_clr}')

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

                    if not self._sub(idx).enable:#m[1]:
                        clr = disabled_clr + text_clr
                self.screen.echo(self.screen_id, self.menu_x + offset, self.menu_y, f'{clr}{title}{self.term.normal}{scr_back_clr}')

                offset += len(title) + self.gap

        if self.sub is not None and self.sub_menu_focus:
            self.sub.on_paint()

    def _sub(self, sel=-1):
        if sel == -1:
            sel = self.selection
        sel_name:str = self.menu[sel][0]
        sel_name = sel_name.replace(' ', '_')
        attr = getattr(self, sel_name)
        return attr

    def run_selection(self):
        sel = self._sub()
        if sel.function is not None:
            sel.function()

    def sub_menu_base_corner(self):
        offset = 0
        for ii in range(self.selection):
            offset += len(self.menu[ii][0]) + self.gap
        self.sub.set_base_corner(self.menu_x + 2 + offset, self.menu_y + 1)

    def child_lose_focus(self):
        self.on_focus(True)
        if self.sub is not None:
            self.sub.on_focus(False)
            self.sub.on_paint()
        self.sub_menu_focus = False
        self.main_wnd.on_paint()
        self.parent.on_paint()


    def __remove_sub_focus(self):
        self.on_focus(True)
        self.sub_menu_focus = False
        self.parent.on_paint()
        if self.sub is not None:
            self.sub.on_focus(False)

    def _next_select(self):
        self.selection += 1
        # self.selection = self.selection % len(self.menu)
        while not self._sub(self.selection % len(self.menu)).enable:
            self.selection += 1
            # self.selection = self.selection % len(self.menu)

    def _prev_select(self):
        self.selection -= 1
        # self.selection = self.selection % len(self.menu)
        while not self._sub(self.selection % len(self.menu)).enable:
            self.selection -= 1
            # self.selection = self.selection % len(self.menu)
        # self.selection -= 1

    def run(self, key=None):
        self.on_paint()
        sub = self._sub()
        self.sub = sub.sub_menu
        if key is not None:
            if self.focus_owner and not self.sub_menu_focus:
                if key.name in self.next_select:
                    self._next_select()
                    # self.selection += 1
                elif key.name == self.prev_select:
                    self._prev_select()
                    # self.selection -= 1
                elif key.name in self.escape:
                    self.parent.child_lose_focus()

                if not self.sub_menu_focus:
                    if key.name == 'KEY_ENTER':
                        if self.sub is not None:
                            self.sub_menu_focus = True
                            self.sub.set_main_wnd(self.main_wnd)
                            self.sub_menu_base_corner()
                            self.sub.on_focus(True)
                            self.sub.run()
                            return None
                        else:
                            self.run_selection()
                            return None
            else:
                if self.sub is not None:
                    key = self.sub.run(key)
                    # return None
        self.selection = self.selection % len(self.menu)
        self.on_paint()
        return key


#############################################################################

class SubMenu(MainMenu):

    # menu = None
    # cnt = 4

    def __init__(self, name=""):
        super().__init__(name)
        # self.term = Terminal()

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

        if not self.focus_owner:
            self.screen.disable_region(self.screen_id)
            return

        # height, width = self.term.height, self.term.width
        scr_back_clr = getattr(self.term, 'on_' + self.background_clr)
        text_clr = getattr(self.term, self.text_clr)
        disabled_clr = getattr(self.term, self.disabled_pos_clr)

        if self.wnd_border:
            # top corners
            self.screen.echo(self.screen_id, self.menu_x, self.menu_y,
                             f'{scr_back_clr}{self.left_top_corner}{self.term.normal}{scr_back_clr}')

            self.screen.echo(self.screen_id, self.menu_x + self.m_width, self.menu_y,
                             f'{scr_back_clr}{self.right_top_corner}{self.term.normal}{scr_back_clr}')

            # bottom corners
            self.screen.echo(self.screen_id, self.menu_x, self.menu_y + self.m_height,
                             f'{scr_back_clr}{self.left_bottom_corner}{self.term.normal}{scr_back_clr}')

            self.screen.echo(self.screen_id, self.menu_x + self.m_width, self.menu_y + self.m_height,
                             f'{scr_back_clr}{self.right_bottom_corner}{self.term.normal}{scr_back_clr}')

            # lines
            # horizontal lines
            for ii in range(0, self.m_width - 1, 1):
                self.screen.echo(self.screen_id, ii + self.menu_x + 1, self.menu_y,
                                 f'{scr_back_clr}{self.hor_line}{self.term.normal}{scr_back_clr}')

                # with self.term.location(ii + self.menu_x + 1, self.menu_y + self.m_height):
                self.screen.echo(self.screen_id, ii + self.menu_x + 1, self.menu_y + self.m_height,
                                 f'{scr_back_clr}{self.hor_line}{self.term.normal}{scr_back_clr}')

            # vertical lines
            for ii in range(self.m_height - 1):
                self.screen.echo(self.screen_id, self.menu_x, self.menu_y + ii + 1,
                                 f'{scr_back_clr}{self.vert_line}{self.term.normal}{scr_back_clr}')

                self.screen.echo(self.screen_id, self.menu_x + self.m_width, self.menu_y + ii + 1,
                                 f'{scr_back_clr}{self.vert_line}{self.term.normal}{scr_back_clr}')

        w = self.m_max_len + 1

        for (idx, m) in enumerate(self.menu):
            title = m[0]
            if idx == self.selection:
                clr = getattr(self.term, self.cursor_back_clr)
            else:
                clr = scr_back_clr + text_clr

            if not self._sub(idx).enable:#m[1]:
                clr = disabled_clr + text_clr

            self.screen.echo(self.screen_id, self.gap_x, self.gap_y + idx, f'{clr}{title:{w}}{self.term.normal}{scr_back_clr}')

        if self.sub is not None and self.sub_menu_focus:
            self.sub.on_paint()