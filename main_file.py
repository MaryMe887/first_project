import os
import sqlite3
from PyQt6.QtCore import Qt
from PyQt6 import uic
import sys
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QInputDialog, QMessageBox


class Tasks(QMainWindow):
    def __init__(self):
        """создание нужных переменных"""
        super().__init__()
        # путь к текущему файлу с кодом
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # загрузка нужного дизайна через полный путь к файлу дизайна
        uic.loadUi(os.path.join(self.base_dir, 'dist', 'ui_files', 'f_project.ui'), self)
        # индекс текущего задания
        self.task_index = 0
        # баллы за правильное выполнение задания. Пригодятся ниже
        self.overall = 0
        # проверка, что задание сделано дл перехода к следующему
        self.flag_done = False
        # сами задания в таблице Tasks, ответы к ним - в Answers
        self.table = sqlite3.connect(os.path.join(self.base_dir, 'dist', 'Users.db'))
        self.cur = self.table.cursor()
        # а теперь в переменной ниже
        self.all_tasks = self.cur.execute(f"""SELECT Tasks.*, Answers.right_ans, Answers.almost_right,
         Answers.annot_right, Answers.annot_almost, Answers.annot_wrong FROM Tasks
        INNER JOIN Answers
            ON Answers.task_id = Tasks.task_id;""").fetchall()
        # здесь будут индексы неправильно сделанных заданий
        self.done_wrong = list()
        self.annotation.setVisible(False)
        # имя пользователя
        self.user_name = self.get_username()
        self.initUI()
        self.set_task()

    def get_username(self):
        """ввод имени поьзователя"""
        while True:
            name, ok_pressed = QInputDialog.getText(self, "Как тебя зовут?",
                                                    "Введите имя для начала игры!! (не пустую строку)")
            # Если пользователь нажал OK и имя не пустое
            if ok_pressed and name != '':
                # Возвращаем имя
                return name
            else:
                QMessageBox.warning(self, "Ошибка", "Ты ввел пустую строку. Попробуй еще раз.")

    def keyPressEvent(self, event):
        """переход к следующему заданию через Enter"""
        if event.key() in (Qt.Key.Key_Enter, 16777220):
            self.next()

    def initUI(self):
        """привязка кнопок к методам"""
        self.setWindowTitle('Уважаемый клиент...')
        for btn in self.ans_btns.buttons():
            btn.clicked.connect(self.checker)
        self.btn_next.clicked.connect(self.next)

    def set_task(self):
        """установка компонентов заданий"""
        self.pixmap = QPixmap(os.path.join(self.base_dir, 'dist', 'pics', self.all_tasks[self.task_index][1]))
        self.prof_pic.setPixmap(self.pixmap)
        self.abon_name.setText(self.all_tasks[self.task_index][2])
        # не воспринимает \n из БД, поэтому заменяем
        self.message.setText(self.all_tasks[self.task_index][3].replace('\\n', '\n'))
        self.ans1.setText(self.all_tasks[self.task_index][4])
        self.ans2.setText(self.all_tasks[self.task_index][5])
        self.ans3.setText(self.all_tasks[self.task_index][6])
        self.right_ans = self.all_tasks[self.task_index][7]
        self.almost_right = self.all_tasks[self.task_index][8]

    def checker(self):
        """Проверка на правильность ответа
           В зависимости от правильности, цвет фона будет изменяться
        """
        if self.flag_done is False:
            if self.sender().objectName() == self.right_ans:
                self.annotation.setText('Правильно!' + self.all_tasks[self.task_index][9].replace('\\n', '\n'))
                self.annotation.setVisible(True)
                self.setStyleSheet("background-color: {}".format('#8CED97'))
                self.overall += 1
            elif self.sender().objectName() == self.almost_right:
                self.annotation.setText('Неплохо...' + self.all_tasks[self.task_index][10].replace('\\n', '\n'))
                self.annotation.setVisible(True)
                self.setStyleSheet("background-color: {}".format('#FEEE6C'))
                self.overall += 0.7
            else:
                self.annotation.setText('Неправильный ответ' + self.all_tasks[self.task_index][11].replace('\\n', '\n'))
                self.annotation.setVisible(True)
                self.setStyleSheet("background-color: {}".format('#FF615C'))
                self.done_wrong.append(self.task_index)
            self.flag_done = True

    def next(self):
        """Проверка, что задание сделано, и переход к следующему заданию"""
        if self.flag_done is True:
            self.task_index += 1
            self.flag_done = False
            self.setStyleSheet("background-color: {}".format('#FFFFFF'))
            self.annotation.setVisible(False)
            if self.task_index == len(self.all_tasks):
                for index in self.done_wrong:
                    self.cur.execute("""INSERT INTO Users(User_name, Done_wrong) VALUES(?, ?)""",
                                     (self.user_name, index))
                self.table.commit()
                self.table.close()
                your_result = Result(self.user_name, round(self.overall, 2) / (len(self.all_tasks) + 1))
                your_result.show()
                self.close()
            self.update()
            self.set_task()
        else:
            self.annotation.setVisible(True)
            self.annotation.setText('Ты еще не выполнил задание!')


class Result(QWidget):
    """Виджет для отображения результата,
       процента правильности работы
    """
    def __init__(self, user, procent):
        super().__init__()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(os.path.join(self.base_dir, 'dist', 'ui_files', 'your_result.ui'), self)
        self.user_name = user
        self.procent = int(procent * 100)
        self.initUi()

    def initUi(self):
        self.setWindowTitle('Результат')
        self.result_procent.setText(str(self.procent) + '%')
        if self.procent >= 65:
            self.pixmap = QPixmap(os.path.join(self.base_dir, 'dist', 'pics', 'nice_dude.png'))
            self.pic.setPixmap(self.pixmap)
        elif self.procent >= 50:
            self.pixmap = QPixmap(os.path.join(self.base_dir, 'dist', 'pics', 'well_good.png'))
            self.pic.setPixmap(self.pixmap)
        else:
            self.pixmap = QPixmap(os.path.join(self.base_dir, 'dist', 'pics', 'dude.png'))
            self.pic.setPixmap(self.pixmap)
        with open('statistics.txt', mode='a') as file:
            # статистика
            file.write(f'{self.user_name} - {str(self.procent)}\n')


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    """Запуск программы"""
    app = QApplication(sys.argv)
    ex = Tasks()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
