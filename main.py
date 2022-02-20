from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtGui import QIcon

import datetime, sys, pyaudio, wave, threading, atexit, sqlite3, os, pygame, numpy as np
pygame.init()
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
    

    def pause(self):
        if (self.stream.is_active()):
            self.stream.stop_stream()
        else:
            self.stream.start_stream()


    def start(self):
        # Очистка ранее записанных аудио
        self.frames = []
        # Запуск потока
        self.stream.start_stream()


    def close(self, time_record):
        # Остановка записи
        with self.lock:
            self.stop = True
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

        # Сохранение записи
        wf = wave.open("list_records/output_sound.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.get_frames()))
        wf.close()

        # Добавление в базу данных
        self.insert_blob("D:\\University\\4_course\\2_semestr\\Design\\Dictaphone\\list_records\\output_sound.wav", time_record)

        # Удаление файла из папки
        os.remove("list_records/output_sound.wav")


    # Конвертация в бинарный файл
    def converter_to_binary_data(self, filename):
        # Конвертировать данные в бинарный формат
        with open(filename, 'rb') as file:
            blob_data = file.read()
        return blob_data
    

    # Вставка в БД
    def insert_blob(self, audio, time):
        try:
            con = sqlite3.connect("Dictaphone.db")
            cur = con.cursor()
            bin_audio = self.converter_to_binary_data(audio)
            query = """INSERT INTO Records (AUDIO, TIME_RECORD) VALUES (?, ?)"""
            data_tuple = ( bin_audio, time)
            cur.execute(query, data_tuple)
            con.commit()
            cur.close()
        except sqlite3.Error as error:
            print('Ошибочка с запросиком к БД...', error)
        finally:
            if con:
                con.close()


class Dictaphone(QtWidgets.QMainWindow):

    def __init__(self):
        super(Dictaphone, self).__init__()# Для доступа к форме
        uic.loadUi('form.ui', self) # Загрузка Ui

        # Счётчик для режима сбережения энергии
        self.count_timer = 0
        self.timer_saving_mode = QtCore.QTimer(self)
        self.timer_saving_mode.setInterval(1000)                                                    
        self.timer_saving_mode.timeout.connect(self.counter_energy_saving)
        self.timer_saving_mode.start()

        # Счётчик для режима сбережения энергии
        self.count_timer_battary = 100
        self.timer_battary = QtCore.QTimer(self)
        self.timer_battary.setInterval(10000)  # 10сек                                                  
        self.timer_battary.timeout.connect(self.counter_timer_battary)
        self.timer_battary.start()

        # Счётчики таймера записи и воспроизведения записи
        self.time_hours = 0
        self.time_minutes = 0
        self.time_seconds = 0

        # Настройка формы
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)                                                    
        self.timer.timeout.connect(self.displayTime)

        self.pushButton_up.setIcon(QIcon("icons/up.png"))
        self.pushButton_up.clicked.connect(self.move_up)
        self.pushButton_right.setIcon(QIcon("icons/right.png"))
        self.pushButton_right.clicked.connect(self.move_right)
        self.pushButton_left.setIcon(QIcon("icons/left.png"))
        self.pushButton_left.clicked.connect(self.move_left)
        self.pushButton_down.setIcon(QIcon("icons/down.png"))
        self.pushButton_down.clicked.connect(self.move_down)

        # Скрытие меню окна
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        
        # Кнопки диктофона
        self.pushButton_play.setIcon(QIcon("icons/play.png"))
        self.pushButton_play.clicked.connect(self.play_audio)
        self.pushButton_record.setIcon(QIcon("icons/record.png"))
        self.pushButton_record.clicked.connect(self.check_DB_records)
        self.pushButton_pause.setIcon(QIcon("icons/pause.png"))
        self.pushButton_pause.clicked.connect(lambda: self.pause_audio(self.timer))
        self.pushButton_delete.setIcon(QIcon("icons/bin.png"))
        self.pushButton_delete.clicked.connect(self.delete_audio)

        # Установка пустого таймера
        self.label_record.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds)))
        self.label_play.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds))) 

        # Отмена сортировки
        self.listWidget.setSortingEnabled(False)
        

    # Включение режима сбережении энергии
    def counter_energy_saving(self):
        self.count_timer += 1
        if self.count_timer == 30:
            self.setStyleSheet("background:lightgray;")
            # Увеличиваем время работы от батареи
            self.timer_battary.setInterval(20000) # 20 сек

    
    # Обнуление счётчика сбережения энергии
    def zeroing_energy_saving(self):
        self.count_timer = 0
        self.setStyleSheet("background:none;")
        # Исходное состояние времени работы батареи
        self.timer_battary.setInterval(10000) # 10 сек


    # Расход батареи
    def counter_timer_battary(self):
        self.count_timer_battary -= 1
        print("Текущий заряд батареи:", self.count_timer_battary)
        if (self.count_timer_battary <= 10):
            self.setEnabled(False)
        elif(self.count_timer_battary > 10):
            self.setEnabled(True)


    # Получение списка записанных файлов
    def get_list_record(self):
        if(self.tabWidget.currentIndex() == 1):
            # Запрос на записанные файлы
            list_times = self.read_blob_data()

            # Очистка layoyt
            self.listWidget.clear()

            # Цикл по файлам папки
            folder = sorted(os.listdir('list_records/'))
            i = 0
            for file in folder:
                if file.endswith('.wav'):
                    #Создание списка
                    id_record = file.split('.')[0] # Номер записи (str)
                    item = QtWidgets.QListWidgetItem()
                    item.setText('Запись_' + id_record + '\t' + list_times[i])
                    self.listWidget.addItem(item)
                    i += 1

    
    # Получение файла из бинарника
    def write_to_file(self, data, filename):
        with open(filename, 'wb') as file:
            file.write(data)


    # Чтение данных из базы данных
    def read_blob_data(self):
        list_times = []
        try:
            con = sqlite3.connect("Dictaphone.db")
            cur =  con.cursor()
            query = """ SELECT * FROM RECORDS"""
            cur.execute(query)
            record = cur.fetchall()
            for row in record:
                audio_path = "D:\\University\\4_course\\2_semestr\\Design\\Dictaphone\\list_records\\" + str(row[0]) + ".wav"
                self.write_to_file(row[1], audio_path)
                list_times.append(row[2])
            cur.close()
        except sqlite3.Error as error:
            print('Ошибочка с запросиком к БД...', error)
        finally:
            if con:
                con.close()
        return list_times


    # Проверка на количество записий (их должно быть не больше 10)
    def check_DB_records(self):
        con = sqlite3.connect('Dictaphone.db')
        cur = con.cursor()
        query = """SELECT count(*)  From Records"""
        cur.execute(query)
        value = cur.fetchall()[0][0]
        if value > 9:
            self.label_record.setText('Нетодасточно памяти.\n Очистите список записей.')
        else:
            self.start_record_audio(self.label_record.text())
            self.start_time_record(self.timer)


    # Начало записи с обнулением счётчиков
    def start_time_record(self, timer):
        if(self.tabWidget.currentIndex() == 1) :
            # Обнуление счётчиков
            if self.time_hours == 0 and self.time_minutes == 0 and self.time_seconds == 0:
                timer.start()  # Запуск таймера
            else:
                timer.stop()
                self.time_hours = 0
                self.time_minutes = 0
                self.time_seconds = 0
                self.label_record.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds)))
        elif(self.tabWidget.currentIndex() == 0):
            self.time_hours = 0
            self.time_minutes = 0
            self.time_seconds = 0
            self.label_play.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds)))
            timer.start()


    # Отображение таймера
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
        if(self.tabWidget.currentIndex() == 1) :
            self.label_record.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds)))  # +++
            self.label_record.adjustSize()
        elif(self.tabWidget.currentIndex() == 0):
            self.label_play.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds)))  # +++
            self.label_play.adjustSize()
            if(datetime.time(self.record_time_hours, self.record_time_minutes, self.record_time_seconds) ==
               datetime.time(self.time_hours, self.time_minutes, self.time_seconds)):
                self.timer.stop()


    # Запись файла
    def start_record_audio(self, time_record):
        # Обнуление счётчика сбережения энергии
        self.zeroing_energy_saving()
        if(self.tabWidget.currentIndex() == 1) :
            if(self.pushButton_record.styleSheet() == "background: lightgray;"):
                self.pushButton_record.setStyleSheet("")
                self.mic.close(time_record)
            else:
                self.pushButton_record.setStyleSheet("background: lightgray;")
                self.mic = MicrophoneRecorder()
                self.mic.start()

    
    # Воспроизведение записанного файла
    def play_audio(self):
        # Обнуление счётчика сбережения энергии
        self.zeroing_energy_saving()

        if (type(self.listWidget.item(self.listWidget.currentRow())) != QtWidgets.QListWidgetItem):
            return
        text_item = self.listWidget.item(self.listWidget.currentRow()).text().split("_")[1].split("\t")[0]
        pygame.mixer.music.load(R"list_records/" + text_item + ".wav")
        pygame.mixer.music.play()

        # Получение длительности записи
        self.record_time_seconds = int(self.listWidget.item(self.listWidget.currentRow()).text().split("\t")[1].split(":")[2])
        self.record_time_minutes = int(self.listWidget.item(self.listWidget.currentRow()).text().split("\t")[1].split(":")[1])
        self.record_time_hours = int(self.listWidget.item(self.listWidget.currentRow()).text().split("\t")[1].split(":")[0])
        self.start_time_record(self.timer)


    # Пауза 
    def pause_audio(self, timer):
        # Обнуление счётчика сбережения энергии
        self.zeroing_energy_saving()

        if self.tabWidget.currentIndex() == 0 and type(self.listWidget.item(self.listWidget.currentRow())) == QtWidgets.QListWidgetItem and datetime.time(self.record_time_hours, self.record_time_minutes, self.record_time_seconds) > datetime.time(self.time_hours, self.time_minutes, self.time_seconds):
            if pygame.mixer.music.get_busy() == True:
                timer.stop()
                pygame.mixer.music.pause()
            else:
                timer.start()
                pygame.mixer.music.unpause()
        elif self.tabWidget.currentIndex() == 1:
            if(self.label_record.text() == ('Нетодасточно памяти.\n Очистите список записей.')):
                return
            else:
                if timer.isActive():
                    timer.stop()
                else:
                    timer.start()
                self.mic.pause()


    # Удалить запись
    def delete_audio(self):
        # Обнуление счётчика сбережения энергии
        self.zeroing_energy_saving()

        # Отмена загрузки воспроизводимой записи
        pygame.mixer.music.unload()

        if (type(self.listWidget.item(self.listWidget.currentRow())) != QtWidgets.QListWidgetItem):
            return
        # Удаление из папки
        os.remove("list_records/" + self.listWidget.item(self.listWidget.currentRow()).text().split("_")[1].split("\t")[0] + ".wav")
        # Удаление из базы
        con = sqlite3.connect("Dictaphone.db")
        cur = con.cursor()
        query = "DELETE FROM RECORDS WHERE ID = ?"
        data_tuple = (self.listWidget.item(self.listWidget.currentRow()).text().split("_")[1].split("\t")[0])
        cur.execute(query, (data_tuple,))
        con.commit()
        cur.close()
        con.close()
         # Удаление из списка
        item = self.listWidget.takeItem(self.listWidget.currentRow())
        self.listWidget.removeItemWidget(item)


    # Стрелка вверх
    def move_up(self):
        # Обнуление счётчика сбережения энергии
        self.zeroing_energy_saving()

        if(self.listWidget.currentRow() == 0):
            self.listWidget.setCurrentRow(self.listWidget.count() - 1)
        else:
            self.listWidget.setCurrentRow(self.listWidget.currentRow() - 1)
    
    
    # Стрелка вправо
    def move_right(self):
        # Обнуление счётчика сбережения энергии
        self.zeroing_energy_saving()

        # Обнуление таймера
        self.time_hours = 0
        self.time_minutes = 0
        self.time_seconds = 0
        self.label_play.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds)))
        # Отмена загрузки воспроизводимой записи
        pygame.mixer.music.unload()
        # Переход
        self.tabWidget.setCurrentIndex(1)


    # Стрелка вниз
    def move_down(self):
        # Обнуление счётчика сбережения энергии
        self.zeroing_energy_saving()

        if(self.listWidget.currentRow() == self.listWidget.count() - 1):
            self.listWidget.setCurrentRow(0)
        else:
            self.listWidget.setCurrentRow(self.listWidget.currentRow() + 1)


    # Стрелка влево
    def move_left(self):
        # Обнуление счётчика сбережения энергии
        self.zeroing_energy_saving()
        # Обнуление таймера
        self.time_hours = 0
        self.time_minutes = 0
        self.time_seconds = 0
        self.label_play.setText(str(datetime.time(self.time_hours, self.time_minutes, self.time_seconds)))
        # Получение списка записей из БД
        self.get_list_record()
        # Переход
        self.tabWidget.setCurrentIndex(0)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Dictaphone()
    window.show()
    app.exec()