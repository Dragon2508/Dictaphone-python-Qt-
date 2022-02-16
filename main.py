from asyncio.windows_events import NULL
from concurrent.futures import thread
from pickle import FALSE
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

import time, datetime
import sys
import pyaudio
import wave

class Record(QtCore.QThread):

    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal()
    isRunning = False
   
    @pyqtSlot()
    def run(self):
        if not self.isRunning:
            self.isRunning = True
            self.progress.emit()
        else:
            self.isRunning = False
            self.finished.emit()

class Dictaphone(QtWidgets.QMainWindow):

    time_hours = 0
    time_minutes = 0
    time_seconds = 0

    def __init__(self, parent=None):
        super(Dictaphone, self).__init__(parent)# Для доступа к форме
        uic.loadUi('form.ui', self) # Загрузка Ui

        # Настройка формы
        timer = QtCore.QTimer(self)
        timer.setInterval(1000)                                                    
        timer.timeout.connect(self.displayTime)

        self.label_center.setPixmap(QPixmap("icons/select.png"))
        self.label_up.setPixmap(QPixmap("icons/up.png"))
        self.label_right.setPixmap(QPixmap("icons/right.png"))
        self.label_down.setPixmap(QPixmap("icons/down.png"))
        self.label_left.setPixmap(QPixmap("icons/left.png"))

        # Скрытие меню окна
        #self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        #self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        # Создание потока для записи звука
        self.record_new = Record()
        self.record_new.progress.connect(self.record_audio)
        self.record_new.finished.connect(self.record_new.deleteLater)
        #thread_new = QThread()
        #record_new.moveToThread(thread_new)
        #thread_new.started.connect(record_new.run)  
        #record_new.finished.connect(record_new.deleteLater)
        #thread_new.finished.connect(thread_new.deleteLater)
        #record_new.finished.connect(thread_new.quit)
        #record_new.progress.connect(self.record_audio)

        
        self.pushButton_play.setIcon(QIcon("icons/play.png"))
        self.pushButton_play.clicked.connect(self.play_audio)
        self.pushButton_record.setIcon(QIcon("icons/record.png"))
        self.pushButton_record.clicked.connect(lambda: self.start_time_record(timer))
        self.pushButton_record.clicked.connect(lambda: self.record_new.start())
        self.pushButton_pause.setIcon(QIcon("icons/pause.png"))
        self.pushButton_pause.clicked.connect(lambda: self.pause_audio(timer))
        self.pushButton_delete.setIcon(QIcon("icons/bin.png"))
        self.pushButton_delete.clicked.connect(self.delete_audio)

        self.widget_play.hide() # Скрытиеэкрана воспроизведения записи
        self.label_record.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds))) # Установка пустого таймера
        
    

    def start_thread(self):
        pass


    def start_time_record(self, timer):
        # Обнуление счётчиков
        if self.time_hours == 0 and self.time_minutes == 0 and self.time_seconds == 0:
            timer.start()  # Запуск таймера
        else:
            timer.stop()
            self.time_hours = 0
            self.time_minutes = 0
            self.time_seconds = 0
            self.label_record.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds)))


    def displayTime(self):
        # Счётчик для секунд, минут, часов
        self.time_seconds += 1
        if self.time_seconds == 60:
            self.time_minutes += 1
            self.time_seconds = 0
        if self.time_minutes == 60:
            self.time_hours += 1
            self.time_minutes = 0

        # Вывод на экран
        self.label_record.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds)))  # +++
        self.label_record.adjustSize()

    
    # Запись файла
    def record_audio(self):
        p = pyaudio.PyAudio()
        chunk = 1024 # Запись кусками по 1024 сэмпла
        sample_format = pyaudio.paInt16 # 16 бит на выборку
        channels = 2
        rate = 44100 # Запись со скоростью 44100 выборок(samples) в секунду
        seconds = 10

        stream = p.open(format=sample_format,# 16 бит на выборку
                        channels=channels,# двухканальная
                        rate=rate,# запись со скоростью 44100 выборок в секунду
                        frames_per_buffer=chunk,# запись кусками по 1024 сэмпла
                        input_device_index=1,# индекс микрофона
                        input=True)# разрешить запись 

        frames = [] # список для хранения кадров

        # Хранить данные в блоках в течении 3 секунд
        for i in range(0, int(rate/chunk * seconds)):
            data = stream.read(1024)
            frames.append(data)

        # Остановить и закрыть поток
        stream.stop_stream()
        stream.close()
        p.terminate()
        self.label_record.setText("Запись окончена!")

        # Сохранить записанные данные в виде файла wav
        wf = wave.open("output_sound.wav", 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(44100)
        wf.writeframes(b''.join(frames))
        wf.close()

    
    # Воспроизведение записанного файла
    def play_audio(self):
        pass


    # Пауза 
    def pause_audio(self, timer):
        if timer.isActive():
            timer.stop()
        else:
            timer.start()

    # Удалить запись
    def delete_audio(self):
        pass
    
    # Стрелка вверх
    def move_up(self):
        pass
    
    # Стрелка вправо
    def move_right(self):
        pass

    # Стрелка вниз
    def move_down(self):
        pass

    # Стрелка влево
    def move_left(self):
        pass

    # Кнопка ДА
    def select_true(self):
        pass

    # Кнопка нет
    def select_false(self):
        pass

    # Режим сбережения
    def saving_mode(self):
        pass


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Dictaphone()
    window.show()
    app.exec()