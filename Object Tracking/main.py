from PyQt5 import QtCore, QtGui, QtWidgets
import cv2 as cv

from ultralytics import YOLO
from sort import Sort
import numpy as np
import threading
#m dang cài venv t, nhưng mà main lại nằm chỗ khác


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(739, 539)
        MainWindow.setStyleSheet("background-color: #F5F5F5;")

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.buttonExit = QtWidgets.QPushButton(self.centralwidget)
        self.buttonExit.setGeometry(QtCore.QRect(620, 480, 101, 31))
        self.buttonExit.setObjectName("buttonExit")
        self.buttonExit.setStyleSheet("""
            QPushButton {
                background-color: #FF6347;
                color: white;
                border-radius: 10px; 
            }
            QPushButton:hover {
                background-color: #FF4500;
            }
            QPushButton:pressed {
                background-color: #FF0000;
            }
        """)
        self.buttonExit.setText("Thoát")
        self.buttonExit.clicked.connect(self.exit_app)

        self.buttonOpen = QtWidgets.QPushButton(self.centralwidget)
        self.buttonOpen.setGeometry(QtCore.QRect(620, 440, 101, 31))
        self.buttonOpen.setObjectName("buttonOpen")
        self.buttonOpen.setStyleSheet("""
            QPushButton {
                background-color: #32CD32;
                color: white;
                border-radius: 10px; 
            }
            QPushButton:hover {
                background-color: #228B22;
            }
            QPushButton:pressed {
                background-color: #006400;
            }
        """)
        self.buttonOpen.setText("Mở/tắt webcam")
        self.buttonOpen.clicked.connect(self.toggle_webcam)

        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(10, 40, 711, 371))
        self.frame.setStyleSheet("""
            background-color: #FFFFFF; 
            border: 2px solid #000000;  
            border-radius: 0px;
        """)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")

        self.webcam_label = QtWidgets.QLabel(self.frame)
        self.webcam_label.setGeometry(QtCore.QRect(0, 0, 711, 371))
        self.webcam_label.setObjectName("webcam_label")
        self.webcam_label.setAlignment(QtCore.Qt.AlignCenter)

        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser.setGeometry(QtCore.QRect(10, 440, 591, 71))
        self.textBrowser.setObjectName("textBrowser")

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(210, 0, 341, 31))
        self.label.setObjectName("label2")
        self.label.setFont(QtGui.QFont("Arial", 20))
        self.label.setText("THEO DÕI CHUYỂN ĐỘNG")

        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(10, 420, 81, 16))
        self.label_2.setObjectName("label_2")
        self.label_2.setFont(QtGui.QFont("Arial", 10))
        self.label_2.setText("Thông báo:")

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.cap = None
        self.running = False


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))

    def toggle_webcam(self):
        if self.running:
            self.running = False  # Tắt webcam
        else:
            self.running = True  # Bật webcam
            threading.Thread(
                target=self.run_webcam).start()  # Chạy webcam trong một thread riêng để không làm treo giao diện

    def exit_app(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
        cv.destroyAllWindows()
        QtCore.QCoreApplication.quit()

    def run_webcam(self):
        model = YOLO('C:\\Dian\\SmartHouse\\Object Tracking\\yolov8n.pt')

        self.cap = cv.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: không thể mở webcam.")
            self.running = False
            return

        frame_width = int(self.cap.get(cv.CAP_PROP_FRAME_WIDTH))
        frame_height = int(self.cap.get(cv.CAP_PROP_FRAME_HEIGHT))

        tracker = Sort()

        roi1_top_left = (0, 0)
        roi1_bottom_right = (frame_width // 2, frame_height)

        roi2_top_left = (frame_width // 2, 0)
        roi2_bottom_right = (frame_width, frame_height)

        def calculate_intersection_area(x1, y1, x2, y2, roi_top_left, roi_bottom_right):
            roi_x1, roi_y1 = roi_top_left
            roi_x2, roi_y2 = roi_bottom_right

            intersect_x1 = max(x1, roi_x1)
            intersect_y1 = max(y1, roi_y1)
            intersect_x2 = min(x2, roi_x2)
            intersect_y2 = min(y2, roi_y2)

            if intersect_x1 < intersect_x2 and intersect_y1 < intersect_y2:
                return (intersect_x2 - intersect_x1) * (intersect_y2 - intersect_y1)
            else:
                return 0

        messages = {}
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self.textBrowser.append("Lỗi: Không thể đọc frame.")
                break

            results = model.track(frame)
            bboxes = []
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    bboxes.append([x1, y1, x2, y2])
            bboxes = np.array(bboxes)

            trackers = tracker.update(bboxes)
            for d in trackers:
                x1, y1, x2, y2, obj_id = map(int, d)
                cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv.putText(frame, str(obj_id), (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

                area_left = calculate_intersection_area(x1, y1, x2, y2, roi1_top_left, roi1_bottom_right)
                area_right = calculate_intersection_area(x1, y1, x2, y2, roi2_top_left, roi2_bottom_right)

                if area_left > area_right:
                    message = f'Đối tượng ID {obj_id} đang ở vùng 1 (bên trái)'
                else:
                    message = f'Đối tượng ID {obj_id} đang ở vùng 2 (bên phải)'
                messages[obj_id] = message

            all_messages = '\n'.join(messages.values())
            QtCore.QMetaObject.invokeMethod(self.textBrowser, "setText", QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(str, all_messages))

            cv.rectangle(frame, roi1_top_left, roi1_bottom_right, (0, 0, 255), 2)
            cv.rectangle(frame, roi2_top_left, roi2_bottom_right, (0, 0, 255), 2)

            rgb_image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
            qt_image = convert_to_Qt_format.scaled(self.webcam_label.width(), self.webcam_label.height(),
                                                   QtCore.Qt.IgnoreAspectRatio)
            self.webcam_label.setPixmap(QtGui.QPixmap.fromImage(qt_image))

        self.cap.release()
        cv.destroyAllWindows()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
