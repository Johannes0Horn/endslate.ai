# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_main_window_v01.ui'
##
## Created by: Qt User Interface Compiler version 5.15.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
    QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
    QPixmap, QRadialGradient)
from PySide2.QtWidgets import *

import ressources_for_QT_rc

class Ui_mainwindow(object):
    def setupUi(self, mainwindow):
        if not mainwindow.objectName():
            mainwindow.setObjectName(u"mainwindow")
        mainwindow.resize(600, 399)
        mainwindow.setMinimumSize(QSize(600, 399))
        mainwindow.setMaximumSize(QSize(600, 399))
        font = QFont()
        font.setKerning(False)
        mainwindow.setFont(font)
        self.background = QLabel(mainwindow)
        self.background.setObjectName(u"background")
        self.background.setGeometry(QRect(0, 0, 601, 401))
        self.background.setPixmap(QPixmap(u":/Main/Resourcefiles/Startupflaeche.png"))
        self.console = QLabel(mainwindow)
        self.console.setObjectName(u"console")
        self.console.setGeometry(QRect(60, 270, 481, 81))
        font1 = QFont()
        font1.setFamily(u"Roboto")
        font1.setPointSize(14)
        font1.setBold(False)
        font1.setItalic(False)
        font1.setWeight(50)
        font1.setKerning(True)
        self.console.setFont(font1)
        self.console.setStyleSheet(u"color:rgb(255, 255, 255)")
        self.console.setTextFormat(Qt.AutoText)

        self.retranslateUi(mainwindow)

        QMetaObject.connectSlotsByName(mainwindow)
    # setupUi

    def retranslateUi(self, mainwindow):
        mainwindow.setWindowTitle(QCoreApplication.translate("mainwindow", u"endslateai", None))
        self.background.setText("")
        self.console.setText(QCoreApplication.translate("mainwindow", u"Hallo", None))
    # retranslateUi

