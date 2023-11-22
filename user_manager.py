import os
import shutil
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidgetItem, QPushButton, QLabel, QMessageBox, QDialog, QVBoxLayout, QProgressBar
from PyQt5.QtCore import pyqtSlot, Qt, QDateTime
from PyQt5.QtGui import QPixmap, QImage
from user_manager_widget import Ui_Widget
from add_user import Add_User_Widget
import sqlite3
from functools import partial
import face_recognition
from pathlib import Path
import pickle

class Train_Dialog(QDialog):
    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle("Attention!")
        # train_dialog.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(800, 500, 180, 40)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(QLabel("Training is Started! Please wait for a minute."))

        self.train_progressbar = QProgressBar()
        self.train_progressbar.setMinimum(0)
        self.train_progressbar.setMaximum(100)
        self.train_progressbar.setFormat('%p%')
        self.layout.addWidget(self.train_progressbar)

        self.max_size = 0
        for root, dirs, files in os.walk('user_face_data'):
            self.max_size += len(files)

    def train_data(self):
        names = []
        encodings = []
        for i, filepath in enumerate(Path('user_face_data').glob("*/*")):
            name = filepath.parent.name
            print(name)
            image = face_recognition.load_image_file(filepath)

            face_encodings = face_recognition.face_encodings(image)

            for encoding in face_encodings:
                names.append(name)
                encodings.append(encoding)
            self.train_progressbar.setValue(int((i+1) / self.max_size * 100))
            QApplication.processEvents()

        names_encodings = {'names': names, 'encodings': encodings}
        with Path('output/encodings.pickle').open('wb') as f:
            pickle.dump(names_encodings, f)
            print('saved')
        
        if QMessageBox.information(self, 'Complete!', 'Training Data Completed!') == QMessageBox.StandardButton.Ok:
            self.close()

class User_Manager_Widget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self._add_user_widget = None
        try:
            self.conn = sqlite3.connect('./attendance_sqlite.db')
            self.cursor = self.conn.cursor()
        except Exception as e:
            QMessageBox.warning(self, 'DB Error!', f'DB Connection error occured: {e}')
            with open('error.log', 'a') as error_log:
                error_log.writelines([f'{QDateTime.currentDateTime().toString("yyyy-mm-dd hh:mm:ss")}: DB Connection error occured: {e}\n'])

        self.display_user_list()

        self.ui.btn_add.clicked.connect(self.btn_add_clicked)
        self.ui.btn_return.clicked.connect(self.btn_return_clicked)
        self.ui.btn_train.clicked.connect(self.btn_train_clicked)

    def display_user_list(self):
        for i in range(self.ui.table_user_list.rowCount()-1, -1, -1):
            self.ui.table_user_list.removeRow(i)
        self.cursor.execute('SELECT * FROM user')
        user_list = self.cursor.fetchall()        
        for row, user in enumerate(user_list):
            print(user)
            self.ui.table_user_list.insertRow(row)
            avatar_img = QImage(user[2])
            label_avatar = QLabel(self.ui.table_user_list.item(row, 0))
            label_avatar.setPixmap(QPixmap().fromImage(avatar_img))
            label_avatar.setGeometry(0, 0, 64, 64)
            self.ui.table_user_list.setCellWidget(row, 0, label_avatar)
            self.ui.table_user_list.setItem(row, 1, QTableWidgetItem(user[0]))
            self.ui.table_user_list.setItem(row, 2, QTableWidgetItem(user[1]))
            btn_delete = QPushButton('Delete')
            btn_delete.setFixedSize(80, 30)
            btn_delete.clicked.connect(partial(self.btn_delete_clicked, row))
            self.ui.table_user_list.setCellWidget(row, 3, btn_delete)
        # self.ui.table_user_list
    @pyqtSlot()
    def btn_delete_clicked(self, row):
        print(row)
        name = self.ui.table_user_list.item(row, 1).text()
        id = self.ui.table_user_list.item(row, 2).text()
        self.cursor.execute("select avatar_url from user where name = ? and id = ?", (name, id))
        avatar_path = self.cursor.fetchone()[0]
        print(avatar_path)
        self.cursor.execute("delete from user where name = ? and id = ?", (name, id))
        self.conn.commit()
        if os.path.exists(avatar_path):
            os.remove(avatar_path)
        
        train_data_path = "user_face_data/" + name + "_" + id
        if os.path.exists(train_data_path):
            shutil.rmtree(train_data_path)
            
        self.display_user_list()
    
    @pyqtSlot()
    def btn_add_clicked(self):
        self._add_user_widget = Add_User_Widget(self)
        self._add_user_widget.ui.btn_return.clicked.connect(self.btn_add_user_widget_return)
        self._add_user_widget.show()
    
    @pyqtSlot()
    def btn_add_user_widget_return(self):
        for i in range(self.ui.table_user_list.rowCount()):
            self.ui.table_user_list.removeRow(i)
        self.display_user_list()

    @pyqtSlot()
    def btn_return_clicked(self):
        self.conn.close()
        self.close()

    @pyqtSlot()
    def btn_train_clicked(self):
        self.train_dialog = Train_Dialog(self)
        self.train_dialog.show()
        self.train_dialog.train_data()
