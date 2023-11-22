import os
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import pyqtSlot, QTimer, Qt, QDateTime
from add_user_widget import Ui_Widget
import cv2
import sqlite3

class Add_User_Widget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.ui.progressBar.setValue(0)

        self.ui.btn_register.clicked.connect(self.btn_register_clicked)
        self.ui.btn_return.clicked.connect(self.btn_return_clicked)

        try:
            self.conn = sqlite3.connect('attendance_sqlite.db')
            self.cursor = self.conn.cursor()
        except Exception as e:
            QMessageBox.warning(self, 'DB Error!', f'DB Connection error occured: {e}')
            with open('error.log', 'a') as error_log:
                error_log.writelines([f'{QDateTime.currentDateTime().toString("yyyy-mm-dd hh:mm:ss")}: DB Connection error occured: {e}\n'])

        self.start_capture = False
        self.capture_path = ''
        self.capture_cnt = 0
        self.image = None
        self.camera_name = 0
        self.detector = None

        if cv2.CascadeClassifier("haarcascade_frontalface_default.xml"):
            self.detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        else:
            self.detector = None
            QMessageBox.warning(self, 'File does not Exist!', f'File error occured: {e}')
            with open('error.log', 'a') as error_log:
                error_log.writelines([f'{QDateTime.currentDateTime().toString("yyyy-mm-dd hh:mm:ss")}: File error occured: {e}\n'])

        if cv2.VideoCapture(self.camera_name):
            self.capture = cv2.VideoCapture(self.camera_name)
        else:
            self.capture = None
            QMessageBox.warning(self, 'Camera Error!', f'Camera Connection error occured: {e}')
            with open('error.log', 'a') as error_log:
                error_log.writelines([f'{QDateTime.currentDateTime().toString("yyyy-mm-dd hh:mm:ss")}: Camera Connection error occured: {e}\n'])

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(10)

    @pyqtSlot()
    def btn_register_clicked(self):
        name = self.ui.lineEdit_name.text()
        id = self.ui.lineEdit_id.text()
        avatar_path = 'avatar/' + name.replace(' ', '_').lower() + '_' + id + '.jpg'
        document = {"name": name, "id": id, "avatar": avatar_path}
        if QMessageBox.information(self, 'Attention', 'Capturing your Avatar!\nPlease look at the Camera.') == QMessageBox.StandardButton.Ok:
            ret, avatar_img = self.capture.read()
            avatar_img = cv2.resize(avatar_img, (64, 64))
            cv2.imwrite(avatar_path, avatar_img)
        self.cursor.execute("insert into user (name, id, avatar_url) value ('{name}', '{id}', '{avatar_path}')")
        self.conn.commit()
        self.start_capture = True
        self.capture_path = '.\\user_face_data\\' + name.replace(' ', '_') + '_' + id
        if not os.path.exists(self.capture_path):
            os.makedirs(self.capture_path)            

    @pyqtSlot()
    def btn_return_clicked(self):
        self.timer.stop()
        self.timer = None
        self.image = None
        self.camera_name = 0
        self.capture.release()
        self.conn.close()
        self.attendacne_db = None
        self.user_collection = None
        self.close()

    def update_frame(self):
        if self.capture != None:
            ret, self.image = self.capture.read()
            self.display_image(self.image)
        
    def display_image(self, image):
        if self.capture_cnt < 20 and self.start_capture == True:
            self.ui.progressBar.setValue((self.capture_cnt + 1)*5)
            cv2.imwrite(self.capture_path + '\\' + str(self.capture_cnt) + '.jpg', image)
            self.capture_cnt += 1
        else:
            self.capture_cnt = 0
            self.start_capture = False

        out_img = self.detect_face(image)
        if len(out_img) != 0:
            for (x, y, w, h) in out_img:
                cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 2)

        qformat = QImage.Format_Indexed8
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        outImage = QImage(image, image.shape[1], image.shape[0], image.strides[0], qformat)
        outImage = outImage.rgbSwapped()

        self.ui.video_screen.setPixmap(QPixmap.fromImage(outImage))
        self.ui.video_screen.setScaledContents(True)
    
    def detect_face(self, img):
        if self.detector != None:
            faces = self.detector.detectMultiScale(img, 1.1, 5)
            return faces
        else:
            return []
