__author__ = 'Richard Foltyn'

import numpy as np
import io

from . import Alignment
from . import TeXFormat


class Table(object):
    def __init__(self, data, header=None, row_labels=None,
                 fmt=None, float_fmt='g', str_fmt='s', align='r',
                 sep_after=None, output_fmt=TeXFormat(booktabs=True)):

        self.data = np.atleast_2d(data)
        self.__header = []
        self.ncol_data = self.data.shape[1]
        self.nrow = self.data.shape[0]
        self.kwargs = {'sep_after': sep_after}

        if row_labels is not None:
            if not isinstance(row_labels, (list, tuple, np.ndarray)):
                row_labels = [row_labels] * self.nrow
            if not isinstance(row_labels, np.ndarray):
                row_labels = np.atleast_2d(np.array(row_labels))

            if row_labels.shape[0] != data.shape[0]:
                if row_labels.shape[1] == data.shape[0]:
                    row_labels = row_labels.T
                else:
                    raise ValueError('Row label and data have non-conformable shape')

            self.ncol_head = row_labels.shape[1]
            row_labels = np.array(row_labels, dtype=object)
            self.data = np.hstack((row_labels, data))
        else:
            self.ncol_head = 0

        self.row_head = row_labels
        self.ncol = self.ncol_head + self.ncol_data

        if header is not None:
            self.append_header(header)

        # column alignment, both header and data
        align_arr = np.atleast_1d(align)
        if align is None or align_arr.shape[0] == 1:
            align = ['l'] * self.ncol_head + ['r'] * self.ncol_data

        assert len(align) == self.ncol

        # Data column formatting
        if fmt is not None:
            lf = len(fmt)
            if lf != self.ncol_data and lf != self.ncol:
                raise ValueError('Format list has non-conformable length')

        # Apply one and only format spec to all data columns
        if fmt is None or (len(fmt) == 1 and self.ncol_data != 1):
            isreal = [np.isreal(x) for x in self.data[0]]
            fmt = list(np.where(isreal, float_fmt, str_fmt))

        # We might need to add format specifiers for label columns, if these
        # are missing.
        if len(fmt) != self.ncol:
            isreal = [np.isreal(x) for x in self.data[0, :self.ncol_head]]
            fmt2 = list(np.where(isreal, float_fmt, str_fmt))
            fmt = fmt2 + fmt

        assert len(fmt) == self.ncol

        self.columns = [Column(align=a, fmt=f) for a, f in zip(align, fmt)]

        if not isinstance(output_fmt, TeXFormat):
            raise NotImplementedError('Output format {} not '
                                      'implemented.'.format(output_fmt))
        self.renderer = output_fmt

    def render(self, file):

        # assert that everything sums up to the same number of columns before
        # rendering anything.

        for hr in self.__header:
            assert hr.ncol == self.ncol

        self.renderer.render(self.data, self.__header, self.columns, file,
                             **self.kwargs)

    def __str__(self):
        s = io.StringIO()
        self.render(s)

        return s.getvalue()

    def append_header(self, header):
        h = HeadRow(header)

        # Try again, accounting for possibly omitted Row label columns
        if h.ncol != self.ncol and self.ncol_head > 0:
            h = HeadRow(header, self.ncol_head)

        if h.ncol != self.ncol:
            raise Exception('Number of header and data columns do not '
                            'match!')

        self.__header.append(h)


class HeadRow(object):
    def __init__(self, cells, ncol_head=0):
        self.__cells = []
        self.ncol = 0

        if ncol_head > 0:
            self.__cells.append(HeadCell('', span=ncol_head))
            self.ncol += ncol_head

        for c in cells:
            if not isinstance(c, HeadCell):
                if isinstance(c, str):
                    kwargs = {'text': c}
                else:
                    kwargs = c
                c = HeadCell(**kwargs)
            self.ncol += c.span
            self.__cells.append(c)

    def __iter__(self):
        for cell in self.__cells:
            yield cell


class HeadCell(object):
    def __init__(self, text, span=1, align=Alignment.center):
        self.text = text
        self.span = span
        self.align = Alignment.parse(align)

    def __str__(self):
        return "HCol('{o.text}', span={o.span}, align={o.align})".format(
            o=self)

    def __repr__(self):
        return self.__str__()


class Column(object):

    def __init__(self, align=Alignment.right, fmt='g'):
        self.fmt = fmt
        self.align = Alignment.parse(align)

    def __str__(self):
        return 'Col({:s}, {{{:s}}})'.format(self.align, self.fmt)

    def __repr__(self):
        return self.__str__()
