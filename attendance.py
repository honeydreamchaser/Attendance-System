import cv2
import requests
import json
import pyttsx3
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import pyqtSlot, QTimer, QDate, Qt, QTime, QDateTime, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from attendance_widget import Ui_Widget
import face_recognition
import pickle
from pathlib import Path
from collections import Counter

class Attendance_Widget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.image = None
        self.capture = None
        self.camera_name = 0
        self.timer = QTimer(self)
        self.auto_stop_timer = QTimer(self)
        self.time_count = 0

        self.date_today = QDate.currentDate()
        self.ui.label_date.setText(self.date_today.toString())
        self.attendance_name_set = set()

        self.start_time = None
        self.end_time = None

        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 100)
        self.voice = self.engine.getProperty("voices")
        print(self.voice)
        self.engine.setProperty("voice", self.voice[1].id)

        self.post_url = 'https://prod.mspeducare.com/mobapi'
        self.headers = {
            'Content-Type': 'application/json'
        }

        self.ui.btn_start.clicked.connect(self.startCapture)
        self.ui.btn_end.clicked.connect(self.stopCapture)
        self.ui.btn_return.clicked.connect(self.btn_return_clicked)

        try:
            with Path('output/encodings.pickle').open('rb') as f:
                self.loaded_encodings = pickle.load(f)
        except Exception as e:
            QMessageBox.warning(self, 'File Error!', f'Could not find trained file: {e}')
            with open('error.log', 'a') as error_log:
                error_log.writelines([f'{QDateTime.currentDateTime().toString("yyyy-mm-dd hh:mm:ss")}: Could not find trained file: {e}\n'])

    @pyqtSlot()
    def btn_return_clicked(self):
        self.capture = None
        self.image = None
        self.timer.stop()
        self.timer = None
        self.auto_stop_timer.stop()
        self.auto_stop_timer = None
        self.close()

    @pyqtSlot()
    def startCapture(self):
        self.start_time = QTime.currentTime()
        self.ui.label_start_time.setText("Start Time: " + self.start_time.toString())
        self.camera_name = 0
        if cv2.VideoCapture(self.camera_name):
            self.capture = cv2.VideoCapture(self.camera_name)
        else:
            self.capture = None
            QMessageBox.warning(self, 'Camera Error!', f'Camera Connection error occured')
            with open('error.log', 'w') as error_log:
                error_log.write(f'{QDateTime.currentDateTime().toString()}: Camera Connection error occured: Please Connect Camera!\n')
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(40)
        self.auto_stop_timer.timeout.connect(self.auto_stop)
        self.auto_stop_timer.start(60000)

    @pyqtSlot()
    def auto_stop(self):
        if self.time_count >= 60:
            self.stopCapture()
            self.time_count = 0
        self.time_count += 1
        print(self.time_count)
    
    @pyqtSlot()
    def stopCapture(self):
        self.capture.release()
        self.end_time = QTime.currentTime()
        self.ui.label_end_time.setText("End Time: " + self.end_time.toString())
        self.timer.stop()
        self.ui.video_screen.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.auto_stop_timer.stop()
        self.time_count = 0
        self.attendance_name_set.clear()
        
    def update_frame(self):
        if self.capture != None:
            ret, self.image = self.capture.read()
            self.display_image(self.image)
        
    def display_image(self, image):
        image = self.detect_face(image)

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
        input_face_locations = face_recognition.face_locations(img, model='hog')
        input_face_encodings = face_recognition.face_encodings(img, input_face_locations)
        for bounding_box, unkown_encoding in zip(input_face_locations, input_face_encodings):
            name = self.recognize_face(unkown_encoding, self.loaded_encodings)
            if not name:
                name = 'Unknown'
            print(name, bounding_box)
            if name != 'Unknown':
                self.time_count = 0
                set_size = len(self.attendance_name_set)
                self.attendance_name_set.add(name)
                if(set_size != len(self.attendance_name_set)):
                    txt_to_spch = "Welcome " + " ".join(name.split('_')[:-1])
                    self.engine.say(txt_to_spch)
                    self.engine.runAndWait()
                    data = {
                        'school_code': 'prod',
                        'user_id': name,
                        'date_time': QDateTime().currentDateTime().toString('yyyy-mm-dd hh:mm')
                    }
                    print(data)
                    json_data = json.dumps(data)
                    response = requests.post(self.post_url, data=json_data, headers=self.headers)

                    if response.status_code == 200:
                        print('Attendance Data posted successfully!')
                    else:
                        self.attendance_name_set.remove(name)
                        print('Error posting json data: ', response.status_code)

            top, right, bottom, left = bounding_box
            cv2.rectangle(img, (left, top), (right, bottom), (255, 0, 0), 2)
            cv2.putText(img, name, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1)
        return img

    def recognize_face(self, unknown_encoding, loaded_encodings):
        boolean_matches = face_recognition.compare_faces(loaded_encodings['encodings'], unknown_encoding)
        votes = Counter(name for match, name in zip(boolean_matches, loaded_encodings['names']) if match)
        if votes:
            return votes.most_common(1)[0][0]