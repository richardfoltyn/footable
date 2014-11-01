__author__ = 'Richard Foltyn'

from enum import Enum


class Alignment(Enum):
    left = 1
    center = 2
    right = 3

    @classmethod
    def parse(cls, value):
        str_to_align = {'l': Alignment.left,
                        'c': Alignment.center,
                        'r': Alignment.right}

        if isinstance(value, Alignment):
            return value
        elif isinstance(value, str):
            s = value[0]
            try:
                return str_to_align[s]
            except KeyError:
                raise ValueError('Invalid alignment string: {}'.format(s))
        elif isinstance(value, int):
            return Alignment(value)
        else:
            raise ValueError('Invalid alignment value: {}'.format(value))

    def __str__(self):
        if self is Alignment.left:
            return 'l'
        elif self is Alignment.center:
            return 'c'
        elif self is Alignment.right:
            return 'r'