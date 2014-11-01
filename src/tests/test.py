__author__ = 'Richard Foltyn'

import numpy as np

import footable as ft

from footable import HeadCell as HC
from footable import Alignment


# Simple table without any headings
data = np.arange(12).reshape((4, -1))
tbl = ft.Table(data)

print(tbl)

# Automatic format detection
data = np.array([['row 1', 1, 1.5], ['row 2', 2.1, 2.0]], dtype=object)
tbl = ft.Table(data)

print(tbl)

# Add a label col
data = np.random.rand(2, 5)
tbl = ft.Table(data, row_labels=['lbl1', 'lbl2'])
print(tbl)

# Add simple header
tbl = ft.Table(data, row_labels=['R1', 'R2'],
               header=['C1', 'C2', 'C3', 'C4', 'C5'])
print(tbl)

# Add header for row labels too
tbl = ft.Table(data, row_labels=['R1', 'R2'],
               header=['Row label', 'C1', 'C2', 'C3', 'C4', 'C5'])
print(tbl)

# Add multicolumn headers
tbl.append_header([HC('C123', span=3, align=Alignment.center),
                   HC('C45', span=2)])

print(tbl)