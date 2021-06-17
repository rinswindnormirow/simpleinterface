import functools

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

