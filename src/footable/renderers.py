__author__ = 'Richard Foltyn'

import numpy as np

from . import Alignment


class OutputFormat(object):

    def render(self, data, headers, columns, file, **kwargs):
        pass


class TeXFormat(OutputFormat):

    mappings = {Alignment.left: 'l', Alignment.center: 'c',
                Alignment.right: 'r'}

    def __init__(self, booktabs=True, cmidrule_trim=True):
        self.booktabs = booktabs
        self.cmidrule_trim = cmidrule_trim

    def render(self, data, headers, columns, file, **kwargs):

        self.render_preamble(columns, file)
        self.render_header(headers, file)
        self.render_data(data, columns, file, **kwargs)
        self.render_epilogue(file)

    def render_preamble(self, columns, file):
        align_str = [self.mappings[c.align] for c in columns]
        print(r'\begin{tabular}{' + ''.join(align_str) + r'}', file=file)
        if self.booktabs:
            print(r'\toprule', file=file)

    def render_epilogue(self, file):
        if self.booktabs:
            print(r'\bottomrule', file=file)

        print(r'\end{tabular}', file=file)

    def render_header(self, headers, file):

        for i, hrow in enumerate(headers):
            offset = 1
            cell_str = []
            rules_str = []
            for j, hcell in enumerate(hrow):
                cell_str.append(self.render_hcell(hcell))
                if hcell.sep and self.booktabs and not hcell.placeholder:
                    tr = ''
                    if self.cmidrule_trim:
                        tr = '(lr)'
                    s = r'\cmidrule%s{%d-%d}' % \
                        (tr, offset, offset + hcell.span - 1)
                    rules_str.append(s)
                offset += hcell.span

            print(' & '.join(cell_str) + r'\\', file=file)
            if len(rules_str) > 0:
                print(' '.join(rules_str), file=file)

        if self.booktabs and len(headers) > 0:
            print(r'\midrule', file=file)

    def render_data(self, data, columns, file, **kwargs):
        sl = kwargs['sep_after']

        nrow = data.shape[0]
        # Convert separator to 1-based indices of rows after which separator
        # should be printed.
        if isinstance(sl, int):
            ls = max(1, sl)
            sl = np.arange(sl-1, nrow, sl)
        else:
            sl = np.unique(sl)

        fmt_list = ['{{arr[{:d}]:{:s}}}'.format(i, o.fmt)
                    for i, o in enumerate(columns)]

        # Identify numeric columns and insert a formatting field for
        # possible minus signs. We want minus signs to be printed as $-$.
        isnum = np.array([c.isnumeric for c in columns], dtype=bool)
        has_num = any(isnum)
        inum = 0
        for i, c in enumerate(columns):
            if c.isnumeric:
                fmt_list[i] = '{{sgn[{:d}]:s}}{:s}'.format(inum, fmt_list[i])
                inum += 1

        fmt_str = ' & '.join(fmt_list) + r' \\'

        inum = np.where(isnum)[0]

        for i in range(nrow):
            x = data[i]
            if has_num:
                # Check which elements are numeric and negative, and insert
                # $-$ in that case.
                neg = x[inum] < 0
                sgn = ['$-$' if x else '' for x in neg]
                # Apply abs. value to all numerical values since sign is
                # taken care of separately.
                x[inum] = np.abs(x[inum])
                print(fmt_str.format(arr=data[i], sgn=sgn), file=file)
            else:
                print(fmt_str.format(arr=data[i]), file=file)

            # Do not print separator after last row as we'll add a bottom rule
            # there.
            do_sep = (i in sl) and i != (nrow-1)

            if self.booktabs and do_sep:
                print(r'\midrule', file=file)

    def render_hcell(self, hcell):
        if hcell.span > 1:
            s = r'\multicolumn{{{o.span}}}{{{a}}}{{{o.text}}}'.format(
                o=hcell, a=self.mappings[hcell.align])
        else:
            s = hcell.text
        return s