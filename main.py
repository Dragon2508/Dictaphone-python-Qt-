from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtGui import QPixmap, QIcon

import datetime, sys, pyaudio, wave, threading, atexit, sqlite3, os, numpy as np

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


    def close(self, value, time_record):

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

        # Добавление в базу данных
        self.insert_blob(value, "output_sound.wav", time_record)

        # Удаление файла из папки
        os.remove("output_sound.wav")

    # Конвертация в бинарный файл
    def converter_to_binary_data(self, filename):
        # Конвертировать данные в бинарный формат
        with open(filename, 'rb') as file:
            blob_data = file.read()
        return blob_data
    
    # Вставка в бд
    def insert_blob(self, id, audio, time):
        try:
            con = sqlite3.connect("Dictaphone.db")
            cur = con.cursor()
            bin_audio = self.converter_to_binary_data(audio)
            query = """INSERT INTO Records (ID, AUDIO, TIME_RECORD) VALUES (?, ?, ?)"""
            data_tuple = (id+1, bin_audio, time)
            cur.execute(query, data_tuple)
            con.commit()
            cur.close()
        except sqlite3.Error as error:
            print('Ошибочка с запросиком к БД...', error)
        finally:
            if con:
                con.close()


class Dictaphone(QtWidgets.QMainWindow):

    time_hours = 0
    time_minutes = 0
    time_seconds = 0

    def __init__(self):
        super(Dictaphone, self).__init__()# Для доступа к форме
        uic.loadUi('form.ui', self) # Загрузка Ui

        # Настройка формы
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)                                                    
        self.timer.timeout.connect(self.displayTime)

        self.label_center.setPixmap(QPixmap("icons/select.png"))
        self.label_up.setPixmap(QPixmap("icons/up.png"))
        self.label_right.setPixmap(QPixmap("icons/right.png"))
        self.label_down.setPixmap(QPixmap("icons/down.png"))
        self.label_left.setPixmap(QPixmap("icons/left.png"))

        # Скрытие меню окна
        #self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        
        self.pushButton_play.setIcon(QIcon("icons/play.png"))
        self.pushButton_play.clicked.connect(self.play_audio)
        self.pushButton_record.setIcon(QIcon("icons/record.png"))
        self.pushButton_record.clicked.connect(self.check_DB_records)
        self.pushButton_pause.setIcon(QIcon("icons/pause.png"))
        self.pushButton_pause.clicked.connect(lambda: self.pause_audio(self.timer))
        self.pushButton_delete.setIcon(QIcon("icons/bin.png"))
        self.pushButton_delete.clicked.connect(self.delete_audio)

        self.label_record.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds))) # Установка пустого таймера
        

    def check_DB_records(self):
        con = sqlite3.connect('Dictaphone.db')
        cur = con.cursor()
        query = """SELECT count(*)  From Records"""
        cur.execute(query)
        value = cur.fetchall()[0][0]
        if value > 9:
            self.label_record.setText('Нетодасточно памяти.\n Очистите список записей.')
        else:
            self.start_record_audio(value, self.label_record.text())
            self.start_time_record(self.timer)

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
    def start_record_audio(self,value, time_record):
        if(self.pushButton_record.styleSheet() == "border: 3px solied black;"):
            self.mic.close(value,time_record)
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
        if(self.label_record.text() == ('Нетодасточно памяти.\n Очистите список записей.')):
            return
        else:
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