from .common import echo
from blessed import Terminal


# @singleton
class Screen:
    screen = {(0, 0): "",}
    region = []
    disabled_region = []
    change_region_cnt: int = 0
    regions_order = []
    base_corner = {}

    def __init__(self):
        self.term = Terminal(force_styling=True)
        # self.log = open('log3.log', 'a')

    def __render(self):
        screen2render = {}
        for ii in self.regions_order:
            region = self.region[ii]
            if not self.disabled_region[ii]:
                for c, s in region.items():
                    # self.log.write(f'reg_id = {ii}, c = {c}, s = {s}\n')
                    if c in self.screen.keys():
                        if c in screen2render.keys() and screen2render[c] != s:
                            screen2render[c] = s
                        else:
                            if s != self.screen[c]:
                                screen2render[c] = s
                    else:
                        screen2render[c] = s
                    self.screen[c] = s

        screen2render = dict(sorted(screen2render.items(), key=lambda x:x[0][1]))
        for c,s in screen2render.items():
            echo(self.term.move(c[1], c[0]) + s)

    def __shift2base(self, c=None, region_id=-1):
        if c is not None and len(c) == 2:
            if region_id != -1 and region_id in self.base_corner.keys():
                base = self.base_corner[region_id]
                return c[0] + base[0], c[1] + base[1]
        return c

    def set_base_corner(self, region_id: int = -1, x=-1, y=-1):
        if region_id > 0 and region_id < len(self.region):
            self.base_corner[region_id] = (x, y)

    def bind(self) -> int:
        self.region.append({})
        self.disabled_region.append(False)
        return len(self.region) - 1

    def begin(self):
        self.change_region_cnt += 1

    def end(self):
        self.change_region_cnt -= 1
        if self.change_region_cnt == 0:
            self.__render()
            self.regions_order = []
            echo(self.term.normal)
        if self.change_region_cnt < 0:
            print("хуйня")
            raise ValueError()

    def disable_region(self, region_id=-1):
        self.disabled_region[region_id] = True

    def echo(self, region_id:int=-1, x=0, y=0, string=""):
        if region_id < 0 or region_id >= len(self.region):
            raise ValueError()

        if region_id not in self.regions_order:
            self.regions_order.append(region_id)

        c = self.__shift2base((x, y), region_id)
        if len(string) > 1:
            ii = 0
            style = u''
            applied_style: bool = False

            while True:
                if ii == len(string): break
                if string[ii] == '\x1b' or string[ii] == '\x0f':
                    if applied_style:
                        style = u''
                        applied_style = False

                    e = string[ii:].find('m')
                    if e != -1:
                        style += string[ii:ii + e + 1]
                        ii += e + 1
                    else:
                        style += string[ii]
                        ii += 1
                    continue

                applied_style = True
                s = style + string[ii]
                c = self.__shift2base((x, y), region_id)
                self.region[region_id][c] = s
                x += 1
                ii += 1
            if applied_style == False and style != u'':
                try:
                    self.region[region_id][c] += style
                except KeyError:
                    self.region[region_id][c] = style
        else:
            self.region[region_id][c] = string

        self.disabled_region[region_id] = False