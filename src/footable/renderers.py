"""
This work is licensed under CC BY 4.0,
https://creativecommons.org/licenses/by/4.0/

Author: Richard Foltyn
"""

import numpy as np
import re

from .enums import Alignment
from .helpers import anything_to_tuple


TEX_ESCAPE_MAP = {
    r'%': r'\%',
    r'&': r'\&'
}

TEX_PATTERN = r'(?<=[^\\])(%|\&)'
TEX_REGEX = re.compile(TEX_PATTERN)


def tex_escape(text: str) -> str:
    """
    Escape TeX special characters in given text.

    Parameters
    ----------
    text : str

    Returns
    -------
    str
    """
    s = TEX_REGEX.sub(lambda match: TEX_ESCAPE_MAP[match.group()], text)
    return s


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

    def render_data(self, data, columns, file, sep=None, nan_char=None,
                    subheadings=None, linespacing=None, **kwargs):
        """
        Render data block of LaTeX table.

        Parameters
        ----------
        data : np.ndarray
        columns : Iterable
        file :
        sep : Sequence of int, optional
        nan_char : str, optional
            String used in place of NaN values.
        subheadings : Iterable of footable.Subheading, optional
        linespacing : Iterable of footable.LineSpacing, optional
        kwargs
        """

        # columns include any row labels!
        nrow, ncol = data.shape

        subheadings = anything_to_tuple(subheadings, force=True)
        linespacing = anything_to_tuple(linespacing, force=True)

        # Use empty list of horizontal separators by default
        if sep is None:
            sep = tuple()

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

        fmt_list = np.array(fmt_list)

        inum = np.where(isnum)[0]

        for i in range(nrow):

            # --- Process any subheading for this row ---

            shs = [sh for sh in subheadings if sh.row == i]
            for sh in shs:
                spacing = anything_to_tuple(sh.spacing, force=True)
                rules = anything_to_tuple(sh.rule, force=True)
                if len(spacing) > 1:
                    print(rf'\addlinespace[{spacing[0]}] ', file=file)

                # Rule above subheader
                if len(rules) > 0:
                    self._render_mid_rule(rules[0], file)

                txt = _apply_style(sh.text, sh.style)
                if ncol > 1:
                    txt = rf'\multicolumn{{{ncol}}}{{{self.mappings[sh.align]}}}{{{txt}}}'
                txt += r' \\'
                print(txt, file=file)

                # Print rule below the subheading
                if len(rules) > 1:
                    self._render_mid_rule(rules[1], file)

                if spacing:
                    print(rf'\addlinespace[{spacing[-1]}] ', file=file)

            x = data[i]

            # TeX: escape all string data
            x = np.array([tex_escape(v) if isinstance(v, str) else v for v in x],
                         dtype=object)

            # Isolate floating-point-type columns, otherwise we cannot call
            # isnan() on an array with dtype=object
            xx = np.array(x[inum], dtype=np.float64)
            # Check if any NaNs are present and if they should be replaced.
            fix_nan = nan_char is not None and np.any(np.isnan(xx))

            fmt_list_i = np.copy(fmt_list)

            if fix_nan:
                inan_fix = inum[np.isnan(xx)]
                # Overwrite formatting for array elements with NaNs
                fmt_list_i[inan_fix] = nan_char
            else:
                fmt_list_i = fmt_list

            fmt_str = ' & '.join(fmt_list_i) + r' \\'

            if has_num:
                # Check which elements are numeric and negative, and insert
                # $-$ in that case.
                neg = x[inum] < 0
                sgn = ['$-$' if x else '' for x in neg]
                # Apply abs. value to all numerical values since sign is
                # taken care of separately.
                x[inum] = np.abs(x[inum])
                txt = fmt_str.format(arr=x, sgn=sgn)
            else:
                txt = fmt_str.format(arr=x)

            # Do quick and dirty LaTeX replacement of %, including only those that
            # are not preceded by \
            txt = re.sub(r'(?<=[^\\])(?P<char>%)', r'\\\g<char>', txt)
            print(txt, file=file)

            # Do not print separator after last row as we'll add a bottom rule
            # there.
            do_sep = (i in sep) and i != (nrow - 1)

            if self.booktabs and do_sep:
                print(r'\midrule', file=file)

            # --- Process line spacing for this row ---

            lspacing = [lsp for lsp in linespacing if lsp.row == i]
            for lsp in lspacing:
                print(rf'\addlinespace[{lsp.height}] ', file=file)

    def render_hcell(self, hcell) -> str:
        text = tex_escape(hcell.text)
        s = r'\multicolumn{{{o.span}}}{{{a}}}{{{text}}}'.format(
            o=hcell, a=self.mappings[hcell.align], text=text)
        return s

    @staticmethod
    def _render_mid_rule(spec, file) -> None:
        """
        Render mid rule in LaTeX table.

        Parameters
        ----------
        spec :
            bool or compatible with specification
        file :
            File handle
        """
        if spec:
            if isinstance(spec, bool):
                # midrule with default width
                print(rf'\midrule', file=file)
            else:
                # midrule with user-specified width
                print(rf'\midrule[{spec}]', file=file)


def _apply_style(text, style=None):
    if not style:
        return text

    style = style.lower()

    if style == 'italic':
        s = rf'\textit{{{text}}}'
    elif style == 'bold':
        s = rf'\textbf{{{text}}}'
    else:
        raise ValueError(f'Unsupported style {style}')

    return s
