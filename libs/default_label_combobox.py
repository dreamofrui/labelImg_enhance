import sys
try:
    from PyQt5.QtWidgets import QWidget, QHBoxLayout, QComboBox, QCompleter
    from PyQt5.QtCore import Qt
except ImportError:
    # needed for py3+qt4
    # Ref:
    # http://pyqt.sourceforge.net/Docs/PyQt4/incompatible_apis.html
    # http://stackoverflow.com/questions/21217399/pyqt4-qtcore-qvariant-object-instead-of-a-string
    if sys.version_info.major >= 3:
        import sip
        sip.setapi('QVariant', 2)
    from PyQt4.QtGui import QWidget, QHBoxLayout, QComboBox, QCompleter
    from PyQt4.QtCore import Qt


class DefaultLabelComboBox(QWidget):
    def __init__(self, parent=None, items=[]):
        super(DefaultLabelComboBox, self).__init__(parent)

        layout = QHBoxLayout()
        self.cb = QComboBox()
        self.items = items
        self.cb.addItems(self.items)

        # Enable editing and auto-completion
        self.cb.setEditable(True)
        self.cb.setInsertPolicy(QComboBox.NoInsert)  # Don't auto-insert typed text into list

        # Setup completer for auto-completion
        completer = QCompleter(self.items)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.cb.setCompleter(completer)

        self.cb.currentIndexChanged.connect(parent.default_label_combo_selection_changed)

        # Also update when user edits the text
        self.cb.editTextChanged.connect(parent.default_label_text_changed)

        layout.addWidget(self.cb)
        self.setLayout(layout)
