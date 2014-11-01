__author__ = 'Richard Foltyn'

import numpy as np

from . import Alignment


class OutputFormat(object):

    def render(self, data, headers, columns, file, **kwargs):
        pass


class TeXFormat(OutputFormat):

    mappings = {Alignment.left: 'l', Alignment.center: 'c',
                Alignment.right: 'r'}

    def __init__(self, booktabs=True):
        self.booktabs = booktabs

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
            cell_str = []
            for j, hcell in enumerate(hrow):
                if hcell.span > 1:
                    s = r'\multicolumn{{{o.span}}}{{{a}}}{{{o.text}}}'.format(
                        o=hcell, a=self.mappings[hcell.align])
                else:
                    s = hcell.text
                cell_str.append(s)

            print(' & '.join(cell_str) + r'\\', file=file)

        if self.booktabs and len(headers) > 0:
            print(r'\midrule', file=file)

    def render_data(self, data, columns, file, **kwargs):
        if 'sep_line' in kwargs:
            sl = int(kwargs['sep_line'])
        else:
            sl = np.inf

        fmt_list = ['{{arr[{:d}]:{:s}}}'.format(i, o.fmt)
                    for i, o in enumerate(columns)]
        fmt_str = ' & '.join(fmt_list) + r' \\'

        for i in range(data.shape[0]):
            print(fmt_str.format(arr=data[i]), file=file)

            if (i + 1) % sl == 0 and self.booktabs:
                print(r'\midrule', file=file)