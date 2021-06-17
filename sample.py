#! /usr/bin/python3

import signal
import json
from simpleinterface import App, MainWindow, SubWindow, SubMenu, MainMenu, Edit, Button, DialogForm

if __name__ == '__main__':

    main_wnd = MainWindow()
    app = App()
    app.set_main_window(main_wnd)
    app.quit_keys = None

    main_wnd.next_sub_wnd = ['KEY_PGUP']
    main_wnd.prev_sub_wnd = ['KEY_PGDOWN']

    left = [15, 15]
    right = [60, 20]

    def create_window():
        app = App()
        sub_wnd = DialogForm()
        sub_wnd.title = "sub window"
        app.mainwindow.attach(sub_wnd)
        sub_wnd.set_base_corner(*left)
        sub_wnd.set_right_corner(*right)
        sub_wnd.escape = ["KEY_ESCAPE"]
        sub_wnd.modal = False

        edit = Edit('хуйня')
        sub_wnd.attach(edit)
        edit.set_base_corner(5, 1)
        edit.size = 30
        edit.on_focus(True)

        sub_wnd.on_focus(True)

        offset = int((right[0] - left[0])/ 2)
        left[0] += offset
        left[1] += 2
        right[0] += offset
        right[1] += 2

    def app_exit():
        app = App()
        app.exit()

    sub_sub_sub_menu_2 = SubMenu("sub_sub_sub_menu_2")
    sub_sub_sub_menu_2.set_menu(
        [["При пожаре", False, None, None],
         ["Воруй", True, None, None],
         ["Убивай", False, None, None],
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
        ["сюда", False, sub_sub_menu, None],
        ["отсюда", True, None, None],
        ["exit", True, None, None]])

    first_sub.exit.function = app_exit

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