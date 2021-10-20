
#from ui_main_window_v01 import Ui_mainwindow
from PySide2.QtWidgets import (QApplication, QProgressBar, QWidget)

import UserInterface.ui_main_window_v01 as ui
from UserInterface.ui_main_window_v01 import Ui_mainwindow

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.ui = Ui_mainwindow()
        self.ui.setupUi(self)

        # go on setting up your handlers like:
        # self.ui.okButton.clicked.connect(function_name)
        # etc...

    def console(self, input):
        self.ui.console.setText(input)