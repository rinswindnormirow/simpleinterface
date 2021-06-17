from blessed import Terminal

class StringBuffer:

    term = Terminal()
    debug = open('string_buf.log', 'w')

    def __init__(self, text_clr, back_clr, screen, screen_id):
        self.__text_color = text_clr
        self.__background_color = back_clr
        self.__screen = screen
        self.__screen_id = screen_id
        self.__cur_pos = 0
        self.__string_buffer = ["", ]
        self.__wx = -1
        self.__wy = -1
        self.__height = -1
        self.__width = -1

        self.debug.write(f'{self.__screen_id} {self.__screen}\n')

    def set_work_size(self, wx, wy, h, w):
        self.__wx = wx
        self.__wy = wy
        self.__height = h
        self.__width = w

    def remove_ch(self, p=0):
        pos = self.__cur_pos
        echo_str = self.__string_buffer[pos][:p] + self.__string_buffer[pos][p+1:]
        self.__string_buffer[pos] = echo_str
        self.string_buffer_render()


    def print(self, string=None, p=-1):
        # self.debug.write('echo ' + f'{string}\n')
        # w = (self.__wx - self.__wx)
        # h  = (self.__wy - self.__wy)
        pos = self.__cur_pos

        echo_str = self.__string_buffer[pos]
        if string is not None:
            if p < 0  or p >= len(echo_str):
                echo_str += string
            else:
                # if p < len(echo_str):
                echo_str = echo_str[:p] + string + echo_str[p:]
            # подгоним строку под размер окна
            # if len(echo_str) > self.__width:
            #     echo_str = echo_str[len(echo_str) - self.__width:]

            next_str = echo_str.find('\n')
            if next_str == -1:
                self.__string_buffer[pos] = echo_str
            else:

                if next_str == len(echo_str) - 1:
                    # \n стоит в конце строки
                    self.__string_buffer[pos] = echo_str[:next_str]
                    self.__string_buffer.append("")
                else:
                    echo_str = string[:next_str]
                    self.__string_buffer[pos] = echo_str

                    echo_str = string[next_str+1:]
                    self.__string_buffer.append(echo_str)

                self.__cur_pos += 1

            if self.__cur_pos == self.__height and self.__height > 1:
                self.__string_buffer.pop(0)
                self.__cur_pos -= 1

        self.string_buffer_render()

    def string_buffer_render(self, _begin=-1, _end=-1):
        # self.debug.write(f'render - {self.__screen_id}\n')
        scr_back_clr = getattr(self.term, 'on_' + self.__background_color)
        text_clr = getattr(self.term, self.__text_color)
        pos = 0
        for s in self.__string_buffer:

            str2render = ""

            if _begin < 0 or _end < 0:

                # подгоним строку под размер окна
                if len(s) > self.__width:
                    str2render = s[len(s) - self.__width:]
                else:
                    str2render = s
            else:
                if _end < len(s):
                    str2render = s[_begin:_end]
                else:
                    str2render = s[_begin:]

            self.__screen.echo(self.__screen_id,
                               self.__wx,
                               self.__wy + pos,
                               f'{scr_back_clr}{text_clr}{str2render}{self.term.normal}{scr_back_clr}')
            pos += 1

    def get_string_buffer_symbol(self, x, y):
        if len(self.__string_buffer) == 0:
            return u''
        if y < 0 or y >= len(self.__string_buffer):
            return u''

        if len(self.__string_buffer[y]) == 0 or x < 0 or x >= len(self.__string_buffer[y]):
            return u''
        return self.__string_buffer[y][x]

    def get_string_len(self, _number):
        if _number >= 0 and _number < len(self.__string_buffer[_number]):
            return len(self.__string_buffer[_number])
        return 0

    def get_buffer_size(self):
        return len(self.__string_buffer)

    def get_string(self, _number):
        if _number >= 0 and _number < len(self.__string_buffer[_number]):
            return self.__string_buffer[_number]
        else:
            return u''