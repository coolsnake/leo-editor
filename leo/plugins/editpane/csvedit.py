import csv
import re
from collections import namedtuple
import leo.core.leoGlobals as g
assert g
from leo.core.leoQt import QtCore, QtWidgets, QtConst, QtGui

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

TableRow = namedtuple('TableRow', 'line row')

DELTA = {  # offsets for selection when moving row/column
    'go-top': (-1, 0),
    'go-bottom': (+1, 0),
    'go-first': (0, -1),
    'go-last': (0, +1)
}

# list of separators to try, need a single chr separator that doesn't
# occur in text
SEPS = [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 47, 58,
59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76,
77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 93, 94, 95,
96, 123, 124, 125, 126, 174, 175, 176, 177, 178, 179, 180, 181, 182,
183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196,
197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210,
211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224,
225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238,
239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252,
253, 254, 46, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78,
79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 97, 98, 99, 100, 101,
102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
116, 117, 118, 119, 120, 121, 122, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57]
SEPS = [chr(i) for i in SEPS]

# import time  # temporary for debugging

def DBG(text):
    """DBG - temporary debugging function

    :param str text: text to print
    """
    print("LEP: %s" % text)

class ListTable(QtCore.QAbstractTableModel):
    """ListTable - a list backed datastore for a Qt Model
    """

    @staticmethod
    def get_table_list(text, sep=',', regex=False):
        """get_table_list - return a list of tables, based
        on number of columns

        :param str text: text
        """

        # look for seperator not in text
        sep_i = 0
        while SEPS[sep_i] in text and sep_i < len(SEPS)-1:
            sep_i += 1
        if sep_i == len(SEPS)-1:
            sep_i=0  # probably not going to work
        rep = SEPS[sep_i]

        if regex:
            text = re.sub(sep, rep, text)
        else:
            text = text.replace(sep, rep)

        reader = csv.reader(StringIO(text), delimiter=rep)
        rows = [TableRow(line=reader.line_num-1, row=row) for row in reader]
        tables = []
        for row in rows:
            if not tables or len(row.row) != len(tables[-1][0].row):
                tables.append([])
            tables[-1].append(row)
        return tables
    def __init__(self, text, tbl, sep=',', regex=False, *args, **kwargs):
        self.tbl = tbl
        self.sep = sep
        self.regex = regex
        self.get_table(text)
        # FIXME: use super()
        QtCore.QAbstractTableModel.__init__(self, *args, **kwargs)

    def get_table(self, text):
        tables = self.get_table_list(text, sep=self.sep, regex=self.regex)
        self.tbl = min(self.tbl, len(tables)-1)
        lines = text.split('\n')
        if tables and tables[self.tbl]:
            self.pretext = lines[:tables[self.tbl][0].line]
            self.posttext = lines[tables[self.tbl][-1].line+1:]
            self.data = [row.row for row in tables[self.tbl]]
        else:
            self.pretext = []
            self.posttext = []
            self.data = []

    def rowCount(self, parent=None):
        return len(self.data) if self.data else 0
    def columnCount(self, parent=None):
        return len(self.data[0]) if self.data and self.data[0] else 0
    def data(self, index, role):
        if role in (QtConst.DisplayRole, QtConst.EditRole):
            return self.data[index.row()][index.column()]
        return None
    def get_text(self):
        out = StringIO()
        writer = csv.writer(out, delimiter=self.sep[0] if self.sep else ',')
        writer.writerows(self.data)
        text = out.getvalue()
        if text.endswith('\n'):
            text = text[:-1]
        text = self.pretext + [text] + self.posttext
        return '\n'.join(text)
    def setData(self, index, value, role):
        self.data[index.row()][index.column()] = value
        self.dataChanged.emit(index, index)
        return True
    def flags(self, index):
        return QtConst.ItemIsSelectable | QtConst.ItemIsEditable | QtConst.ItemIsEnabled

class LEP_CSVEdit(QtWidgets.QWidget):
    """LEP_PlainTextEdit - simple LeoEditorPane editor
    """
    lep_type = "EDITOR-CSV"
    lep_name = "CSV Editor"
    def __init__(self, c=None, lep=None, *args, **kwargs):
        """set up"""
        super(LEP_CSVEdit, self).__init__(*args, **kwargs)
        self.c = c
        self.lep = lep
        self.tbl = 0
        self.ui = self.make_ui()
    def make_ui(self):
        """make_ui - build up UI"""

        ui = type('CSVEditUI', (), {})
        self.setLayout(QtWidgets.QVBoxLayout())
        buttons = QtWidgets.QHBoxLayout()
        self.layout().addLayout(buttons)
        buttons2 = QtWidgets.QHBoxLayout()
        self.layout().addLayout(buttons2)

        def mkbuttons(what, function):

            list_ = [
                ('go-first', "%s column left", QtWidgets.QStyle.SP_ArrowLeft),
                ('go-last', "%s column right", QtWidgets.QStyle.SP_ArrowRight),
                ('go-top', "%s row above", QtWidgets.QStyle.SP_ArrowUp),
                ('go-bottom', "%s row below", QtWidgets.QStyle.SP_ArrowDown),
            ]

            buttons.addWidget(QtWidgets.QLabel(what+": "))
            for name, tip, fallback in list_:
                button = QtWidgets.QPushButton()
                button.setIcon(QtGui.QIcon.fromTheme(name,
                    QtWidgets.QApplication.style().standardIcon(fallback)))
                button.setToolTip(tip % what)
                button.clicked.connect(lambda checked, name=name: function(name))
                buttons.addWidget(button)

        mkbuttons("Move", self.move)
        mkbuttons("Insert", self.insert)

        for text, function, layout in [
            ("Del row", lambda clicked: self.delete_col(row=True), buttons),
            ("Del col.", lambda clicked: self.delete_col(), buttons),
            ("Prev", lambda clicked: self.prev_tbl(), buttons2),
            ("Next", lambda clicked: self.prev_tbl(next=True), buttons2),
        ]:
            btn = QtWidgets.QPushButton(text)
            layout.addWidget(btn)
            btn.clicked.connect(function)

        ui.min_rows = QtWidgets.QSpinBox()
        buttons2.addWidget(ui.min_rows)
        ui.sep_txt = QtWidgets.QLineEdit(',')
        buttons2.addWidget(QtWidgets.QLabel("Sep:"))
        buttons2.addWidget(ui.sep_txt)
        ui.regex_sep = QtWidgets.QCheckBox("regex.")
        buttons2.addWidget(ui.regex_sep)
        ui.min_rows.setMinimum(1)
        ui.min_rows.setPrefix("tbl with ")
        ui.min_rows.setSuffix(" rows")
        ui.min_rows.setValue(4)

        buttons.addStretch(1)

        ui.table = QtWidgets.QTableView()
        self.layout().addWidget(ui.table)
        return ui

    def delete_col(self, row=False):
        d = self.ui.data.data
        index = self.ui.table.currentIndex()
        r = index.row()
        c = index.column()
        if r < 0 or c < 0:
            return  # no cell selected
        if row:
            d[:] = d[:r] + d[r+1:]
        else:
            d[:] = [d[i][:c] + d[i][c+1:] for i in range(len(d))]
        self.update_text(self.new_data())
        self.ui.table.setCurrentIndex(self.ui.data.index(r, c))
    def insert(self, name, move=False):
        index = self.ui.table.currentIndex()
        row = None
        col = None
        r = index.row()
        c = index.column()
        if move and (r < 0 or c < 0):
            return  # no cell selected
        d = self.ui.data.data
        if name == 'go-top':
            # insert at row, or swap a and b for move
            if move and r == 0:
                return
            row = r
            a = r-1
            b = r
        if name == 'go-bottom':
            row = r + 1
            a = r
            b = r+1
        if row is not None:
            if move:
                d[:] = d[:a] + [d[b], d[a]] + d[b+1:]
            else:
                d[:] = d[:row] + [[''] * len(d[0])] + d[row:]
            self.update_text(self.new_data())

        if name == 'go-first':
            if move and c == 0:
                return
            col = c
            a = c-1
            b = c
        if name == 'go-last':
            col = c + 1
            a = c
            b = c+1
        if col is not None:
            if move:
                d[:] = [
                    d[i][:a] + [d[i][b], d[i][a]] + d[i][b+1:]
                    for i in range(len(d))
                ]
            else:
                d[:] = [
                    d[i][:col] + [''] + d[i][col:]
                    for i in range(len(d))
                ]
            self.update_text(self.new_data())

        if move:
            r = max(0, r+DELTA[name][0])
            c = max(0, c+DELTA[name][1])
        self.ui.table.setCurrentIndex(self.ui.data.index(r, c))
        self.ui.table.setFocus(QtConst.OtherFocusReason)

    def move(self, name):
        self.insert(name, move=True)
    def prev_tbl(self, next=False):
        text = self.ui.data.get_text()
        tables = ListTable.get_table_list(text, sep=self.ui.sep_txt.text(), regex=self.ui.regex_sep.isChecked())
        self.tbl += 1 if next else -1
        while 0 <= self.tbl <= len(tables)-1:
            if len(tables[self.tbl]) >= self.ui.min_rows.value():
                break
            self.tbl += 1 if next else -1
        self.tbl = min(max(0, self.tbl), len(tables)-1)
        self.update_text(text)
    def focusInEvent (self, event):
        QtWidgets.QTextEdit.focusInEvent(self, event)
        DBG("focusin()")
        self.lep.edit_widget_focus()
        #X self.update_position(self.lep.get_position())

    def focusOutEvent (self, event):
        QtWidgets.QTextEdit.focusOutEvent(self, event)
        DBG("focusout()")
    def new_data(self, top_left=None, bottom_right=None, roles=None):
        text = self.ui.data.get_text()
        self.lep.text_changed(text)
        return text
    def new_text(self, text):
        """new_text - update for new text

        :param str text: new text
        """
        tables = ListTable.get_table_list(text, sep=self.ui.sep_txt.text(), regex=self.ui.regex_sep.isChecked())
        self.tbl = 0
        # find largest table, or first table of more than n rows
        for i in range(1, len(tables)):
            if len(tables[i]) > len(tables[self.tbl]):
                self.tbl = i
            if len(tables[self.tbl]) > self.ui.min_rows.value():
                break
        self.update_text(text)

    def update_text(self, text):
        """update_text - update for current text

        :param str text: current text
        """
        DBG("update editor text")
        self.ui.data = ListTable(text, self.tbl, sep=self.ui.sep_txt.text(), regex=self.ui.regex_sep.isChecked())
        self.ui.data.dataChanged.connect(self.new_data)
        self.ui.table.setModel(self.ui.data)
