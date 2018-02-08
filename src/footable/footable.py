__author__ = 'Richard Foltyn'

import numpy as np
import io
import collections

from . import Alignment
from . import TeXFormat


def as_list(val):
    if isinstance(val, list):
        return val
    elif isinstance(val, collections.Iterable):
        return list(val)
    else:
        return [val]


class Table(object):
    def __init__(self, data, header=None, row_labels=None,
                 fmt=None, float_fmt='g', str_fmt='s', align=None,
                 sep_after=None, sep_every=None, sep=None,
                 output_fmt=TeXFormat(booktabs=True),
                 nan_char='--'):
        """
        Create Table object with given properties.

        Parameters
        ----------
        data : array_like
        header : list
        row_labels : list
        fmt : list or str
            List of column-specific format strings
        float_fmt : str
        str_fmt : str
        align : Alignment or list
            Column alignment specification
        sep_after : int or array_like
            Only present for backward compatibility.
            Use sep or sep_every instead.
        sep_every = int
            If not None, specifies the number of rows after which a
            horizontal rule should be inserted. Ignored if argument `sep` is
            not None.
        sep : int or array_like
            If not None, specifies the list of rows after which horizontal
            rules should be inserted. Overrides argument `sep_every`.
            Note: Values are interpreted as zero-based row indices.
        nan_char : str or None
            If not None, character to insert into table cells whenever the
            underlying data element is floating point an np.isnan evaluates
            to true.
        output_fmt :
        """

        self.data = np.atleast_2d(data)

        assert self.data.shape[1] > 0 and self.data.shape[0] > 0

        self.__header = []
        self.ncol_data = self.data.shape[1]
        self.ncol_head = 0
        self.nrow = self.data.shape[0]

        # Consolidate horizontal rule arguments into a list of rows after
        # which separators should be inserted.
        if sep is not None:
            sep = np.unique(sep)
        elif sep_every is not None:
            sep_every = int(sep_every)
            sep = np.arange(sep_every-1, self.nrow, sep_every)
        elif sep_after is not None:
            # For backward compatibility, interpret the meaning of `sep_after`
            # depending on whether it's an integer or something else.
            # For integer values, we assume the same meaning as `sep_every`,
            # and interpret it as `sep` otherwise.
            if isinstance(sep_after, int):
                sep_every = int(sep_after)
                sep = np.arange(0, self.nrow, sep_every)
            else:
                sep = np.unique(sep_after)

        # kwargs passed to renderer
        self.kwargs = {'sep': sep, 'nan_char': nan_char}

        # validate arguments
        '{{:{:s}}}'.format(float_fmt).format(1.0)
        '{{:{:s}}}'.format(str_fmt).format('a')

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

        self.row_head = row_labels
        self.ncol = self.ncol_head + self.ncol_data

        if header is not None:
            self.append_header(header)

        # column alignment, both header and data
        if align is not None:
            align = as_list(align)
            # Attempt to parse alignment values
            align = [Alignment.parse(x) for x in align]

            # Got only one values, this must be for data columns. Project to
            # all other data columns and add alignment for row labels if
            # required.
            if len(align) == 1:
                align = ['l'] * self.ncol_head + align * self.ncol_data

            # align list has length of col(data) > 1, or some other length.
            # Try adding alignment for row labels have alignment values for
            # all columns.
            if len(align) == self.ncol_data and self.ncol_head > 0:
                align = ['l'] * self.ncol_head + align

            if len(align) != self.ncol:
                raise ValueError('Alignment length not compatible with '
                                 'data array')
        else:
            align = ['l'] * self.ncol_head + ['r'] * self.ncol_data

        # Data column formatting
        if fmt is not None:
            fmt = as_list(fmt)

            if len(fmt) == 1:
                fmt = fmt * self.ncol_data

            # We are missing formatting for row labels, so infer these from data
            # types.
            if len(fmt) == self.ncol_data and self.ncol_head > 0:
                isreal = [np.isreal(x) for x in self.data[0, :self.ncol_head]]
                fmt_lbl = list(np.where(isreal, float_fmt, str_fmt))
                fmt = fmt_lbl + fmt

            if len(fmt) != self.ncol:
                raise ValueError('Format length not compatible with data array')
        else:
            # Infer default formatting from column data types for both row label
            # and data columns.
            isreal = [np.isreal(x) for x in self.data[0]]
            fmt = list(np.where(isreal, float_fmt, str_fmt))

        assert len(fmt) == self.ncol
        assert len(align) == self.ncol

        isreal = [np.isreal(x) for x in self.data[0]]
        self.columns = [Column(align=a, fmt=f, isnumeric=ir)
                        for a, f, ir in zip(align, fmt, isreal)]

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
            self.__cells.append(HeadCell('', span=ncol_head, placeholder=True))
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
    def __init__(self, text, span=1, align=Alignment.center, sep=None,
                 placeholder=False):
        self.span = span
        self.align = Alignment.parse(align)
        self.placeholder = placeholder
        self.text = text

        if self.placeholder:
            self.text = ''

        # By default, only show bottom separator for cells spanning more than
        # one column
        self.sep = (sep is None and self.span > 1) or sep

    def __str__(self):
        return "HCol('{o.text}', span={o.span}, align={o.align})".format(
            o=self)

    def __repr__(self):
        return self.__str__()


class Column(object):

    def __init__(self, align, fmt, isnumeric=True):
        self.fmt = fmt
        self.align = Alignment.parse(align)
        self.isnumeric = isnumeric

    def __str__(self):
        return 'Col({:s}, {{{:s}}})'.format(self.align, self.fmt)

    def __repr__(self):
        return self.__str__()
