import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSlot, Qt
from main_widget import Ui_Widget
from attendance import Attendance_Widget
from user_manager import User_Manager_Widget

class Main_Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self._attendance_widget = None
        self._add_student_widget = None
        self.ui.btn_start_attendance.clicked.connect(self.btn_start_attendance_clicked)
        self.ui.btn_add_new_student.clicked.connect(self.btn_add_new_student_clicked)
        self.ui.btn_exit.clicked.connect(self.close)
    
    @pyqtSlot()
    def btn_start_attendance_clicked(self):
        self._attendance_widget = Attendance_Widget(self)
        self._attendance_widget.show()

    @pyqtSlot()
    def btn_add_new_student_clicked(self):
        self._add_student_widget = User_Manager_Widget(self)
        self._add_student_widget.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = Main_Widget()
    ui.show()
    sys.exit(app.exec_())