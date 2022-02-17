from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtGui import QPixmap, QIcon

import datetime, sys, pyaudio, wave, threading, atexit, numpy as np

class MicrophoneRecorder(object):

    
    def __init__(self, rate=44100, chunksize=1024):
        self.rate = rate
        self.chunksize = chunksize
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=self.rate,
                                  input=True,
                                  frames_per_buffer=self.chunksize,
                                  stream_callback=self.new_frame)
        self.lock = threading.Lock()
        self.stop = False
        self.frames = []
        atexit.register(self.close)


    def new_frame(self, data, frame_count, time_info, status):
        #data = np.fromstring(data, 'int16')
        data = np.frombuffer(data, 'int16')
        with self.lock:
            self.frames.append(data)
            if self.stop:
                return None, pyaudio.paComplete
        return None, pyaudio.paContinue
    

    def get_frames(self):
        with self.lock:
            frames = self.frames
            self.frames = []
            return frames
    

    def start(self):
        # Очистка ранее записанных аудио
        self.frames = []
        # Запуск потока
        self.stream.start_stream()


    def close(self):
        # Остановка записи
        with self.lock:
            self.stop = True
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        # Сохранение записи
        wf = wave.open("output_sound.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.get_frames()))
        wf.close()


class Dictaphone(QtWidgets.QMainWindow):

    time_hours = 0
    time_minutes = 0
    time_seconds = 0

    def __init__(self):
        super(Dictaphone, self).__init__()# Для доступа к форме
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
        #self.record_new = Record()
        #self.record_new.progress.connect(self.record_audio)
        #self.record_new.finished.connect(self.record_new.deleteLater)
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
        self.pushButton_record.clicked.connect(lambda: self.start_record_audio())
        self.pushButton_pause.setIcon(QIcon("icons/pause.png"))
        self.pushButton_pause.clicked.connect(lambda: self.pause_audio(timer))
        self.pushButton_delete.setIcon(QIcon("icons/bin.png"))
        self.pushButton_delete.clicked.connect(self.delete_audio)

        self.widget_play.hide() # Скрытиеэкрана воспроизведения записи
        self.label_record.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds))) # Установка пустого таймера
        

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
    def start_record_audio(self):
        if(self.pushButton_record.styleSheet() == "border: 3px solied black;"):
            self.mic.close()
            self.pushButton_record.setStyleSheet("")
        else:
            self.mic = MicrophoneRecorder()
            self.mic.start()
            self.pushButton_record.setStyleSheet("border: 3px solied black;")

    
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