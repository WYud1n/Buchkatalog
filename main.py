import sqlite3
import csv
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog, QInputDialog, QMessageBox

flag_0 = False


class Main(QMainWindow):
    def __init__(self):
        global flag_0
        super().__init__()
        uic.loadUi('User_Interface.ui', self)

        if flag_0:
            self.default_query()

        self.data = []

        self.PB_update.clicked.connect(self.default_query)
        self.PB_add.clicked.connect(self.item_add)
        self.PB_open.clicked.connect(self.set_connection)
        self.PB_csv.clicked.connect(self.save_2_csv)
        self.PB_del.clicked.connect(self.item_del)
        self.PB_save.clicked.connect(self.save_2_sqlite)
        self.tableWidget.itemDoubleClicked.connect(self.item_changing)
        self.comboBox.currentTextChanged.connect(self.sort_columns)
        self.lineEdit.textChanged.connect(self.search)

    def set_connection(self):
        global flag_0
        self.file = QFileDialog.getOpenFileName(self, 'Выбрите SQLite файл', '')[0]
        if self.file:
            self.connection = sqlite3.connect(self.file)
            flag_0 = True
            self.default_query()

    def default_query(self):
        try:
            self.query = '''Select  Arbeit.Name, Autoren.Autor, Bucher.Name_des_Buches, 
            Bucher.Lage, Bucher.Verlag, Bucher.Erscheinungsjahr, Bucher.Seitenzahl, Bucher.ISBN 
            From Bucher
             left join Arbeit on Bucher.ID = Arbeit.ID_Bucher 
             left join Autoren on Arbeit.ID_Autor = Autoren.ID'''
            self.data = self.connection.cursor().execute(self.query).fetchall()
        except Exception as e:
            if e.__class__.__name__ == 'DatabaseError':
                self.log('Это не база данных!')
            if e.__class__.__name__ == 'OperationalError':
                self.log('Эта база данных не подходит программе!')
        else:
            self.update_table_widget(self.data)
            if self.lineEdit.text():
                self.lineEdit.setText('')

    def update_table_widget(self, data):
        self.tableWidget.setRowCount(0)
        for i, row in enumerate(data):
            self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(elem)))
        self.tableWidget.resizeColumnsToContents()
        try:
            self.sort_columns()
        except TypeError:
            pass
        self.log('Таблица успешно обновлена')

    def item_add(self):
        what, ok_pressed = QInputDialog.getItem(
            self, "Добавить", "Что Вы хотите добавить?\n\nПравильный порядок добавления:\n"
                              "1) Автор\n2) Книга\n3) Произведение",
            ("Автора", "Книгу", "Произведение"), 0, False)
        if ok_pressed:
            try:
                if what == 'Автора':
                    self.dialog = AddAuthor(self.connection)
                    self.dialog.show()
                if what == 'Книгу':
                    self.dialog = AddBook(self.connection)
                    self.dialog.show()
                if what == 'Произведение':
                    self.dialog = AddWork(self.connection)
                    self.dialog.show()
            except AttributeError as e:
                self.log('Сначала откройте базу данных!')
            else:
                self.log('Элемент успешно добавлен')

    def item_changing(self):
        row = self.tableWidget.currentRow()
        col = self.tableWidget.currentColumn()
        item = self.tableWidget.currentItem()
        if row == -1 and col == -1 and not item:
            pass
        else:
            if col == 1:
                self.dialog = EditAuthor(self.data[row][col], self.connection)
                self.dialog.show()
            if col == 0:
                self.dialog = EditWork(self.data[row][col], self.connection)
                self.dialog.show()
            if col > 1:
                self.dialog = EditBook(self.data[row][2:], self.connection)
                self.dialog.show()
                self.log('Элемент успешно изменён')

    def item_del(self):
        try:
            col = self.tableWidget.currentColumn()
            row = self.tableWidget.currentRow()

            self.mbox = QMessageBox(self)
            self.mbox.setWindowTitle('Подтвердите')
            self.mbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            if 2 <= col <= 7:
                self.mbox.setText("Вы действительно хотите удалить эту книгу?")
            elif col == 0:
                self.mbox.setText("Вы действительно хотите удалить это произведение?")
            elif col == 1:
                self.mbox.setText("Вы действительно хотите удалить этого автора?")
            self.mbox.setIcon(QMessageBox.Question)
            res = self.mbox.exec()
            if res == QMessageBox.No:
                pass
            else:
                if row >= 0:
                    if 2 <= col <= 7:
                        work = self.data[row]
                        ISBN = work[-1]

                        self.connection.execute('''delete from Arbeit
                        where ID = (select Arbeit.ID from Arbeit
                        left join Bucher on Arbeit.ID_Bucher = Bucher.ID
                        where Bucher.ISBN = ?)''', (ISBN,))

                        self.connection.execute('''delete from Bucher
                        where Bucher.ISBN = ?''', (ISBN,))
                    elif col == 0:
                        work_row = self.data[row]
                        author = work_row[1]
                        work = work_row[0]
                        self.connection.cursor().execute(f'''delete from Arbeit 
                        where ID = (select Arbeit.ID 
                        from Arbeit left join Autoren on Arbeit.ID_Autor = Autoren.ID 
                        where Autoren.Autor = "{author}" and Arbeit.Name = "{work}")''')
                    elif col == 1:
                        author = self.tableWidget.currentItem().text()
                        self.connection.execute('''Delete from Bucher
                        where ISBN in (select Bucher.ISBN from Bucher
                        left join Arbeit on Arbeit.ID_Bucher = Bucher.ID
                        left join Autoren on Autoren.ID = Arbeit.ID_Autor
                        where Autoren.Autor = ?)''', (author,))

                        self.connection.execute('''delete from Arbeit
                        where ID in (select Arbeit.ID from Arbeit
                        left join Autoren on Autoren.ID = Arbeit.ID_Autor
                        where Autoren.Autor = ?)''', (author,))

                        self.connection.execute('''delete from Autoren
                        where Autor = ?''', (author,))
        except Exception as e:
            self.log(e)
        else:
            self.log('Элемент успешно удалён')
            self.default_query()

    def save_2_csv(self):
        global flag_0
        if flag_0:
            file = QFileDialog.getSaveFileName(self, 'CSV save', '', 'CSV (*.csv)')[0]
            if file:
                self.default_query()
                with open(file, 'w', newline='', encoding="windows-1251") as csv_file:
                    writer = csv.writer(csv_file, delimiter=';', quotechar='"',
                                        quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(
                        ["Произведение", "Автор", "Книга", "Стеллаж/Полка", "Издание", "Год",
                         "Страницы", "ISBN"])
                    for i in self.data:
                        writer.writerow(i)
        else:
            self.log('Сначала откройте базу данных!')

    def save_2_sqlite(self):
        global flag_0
        if flag_0:
            self.connection.commit()
        self.connection = sqlite3.connect(self.file)
        self.default_query()

    def sort_columns(self):
        columns_list = ['Произведению', 'Автору', 'Книге', 'Месту', 'Изданию', 'Году', 'Страницам',
                        'ISBN']
        column = columns_list.index(self.comboBox.currentText())
        self.tableWidget.sortItems(column)
        if self.data:
            self.data.sort(key=lambda x: x[column])

    def log(self, text):
        self.L_log.setText(text)

    def search(self):
        text = self.lineEdit.text().capitalize()
        my_list_1 = ['Произведению', 'Автору', 'Книге', 'Изданию', 'ISBN']
        my_list_2 = ['Arbeit.Name', 'Autoren.Autor', 'Bucher.Name_des_Buches', 'Bucher.Verlag',
                     'Bucher.ISBN']
        try:
            i = my_list_1.index(self.comboBox.currentText())
            if len(text) > 3:
                data = self.connection.cursor().execute(
                    self.query + f" where {my_list_2[i]} like '{text}%'")
                self.update_table_widget(data)
        except ValueError:
            pass

    def resizeEvent(self, event):
        w = self.width()
        h = self.height()
        self.L_log.move(10, h - 85)
        self.tableWidget.resize(w - 18, h - 175)

    def closeEvent(self, event):
        global flag_0
        if flag_0:
            self.connection.commit()


class AddAuthor(QMainWindow):
    def __init__(self, connection):
        super().__init__()
        uic.loadUi('Dialog_Author.ui', self)
        self.PB_ready.clicked.connect(self.save)
        self.PB_cancel.clicked.connect(self.close)
        self.connection = connection

    def save(self):
        temp = [self.LE_surname.text(), self.LE_name.text(), self.LE_patronymic.text()]
        if temp[0] or temp[1]:
            if temp[2]:
                author = f'{temp[0]} {temp[1][0]}. {temp[2][0]}.'
            else:
                author = temp[0] + ' ' + temp[1]

            self.connection.cursor().execute('INSERT INTO Autoren(Autor) VALUES(?)', (author,))

            ex.default_query()
            self.close()
        else:
            self.LE_surname.setText('Введите фамилию!!!')
            self.LE_name.setText('Введите имя!!!')


class AddBook(QMainWindow):
    def __init__(self, connection):
        super().__init__()
        uic.loadUi('Dialog_Book.ui', self)
        self.PB_ready.clicked.connect(self.save)
        self.PB_cancel.clicked.connect(self.close)
        self.connection = connection

    def save(self):
        if self.LE_ISBN.text():
            temp = [self.LE_name.text(), self.LE_ISBN.text(), self.LE_ph.text(),
                    self.LE_pages.text(),
                    self.LE_year.text(), self.LE_location.text()]

            self.connection.cursor().execute('INSERT INTO Bucher(Name_des_Buches,ISBN,Verlag,'
                                             'Seitenzahl'
                                             ',Erscheinungsjahr,Lage) VALUES(?,?,?,?,?,?)',
                                             (temp[0], temp[1], temp[2], temp[3], temp[4], temp[5]))

            ex.default_query()
            self.close()
        else:
            self.LE_ISBN.setText('Введите ISBN!!!')


class AddWork(QMainWindow):
    def __init__(self, connection):
        super().__init__()
        uic.loadUi('Dialog_Work.ui', self)
        self.PB_ready.clicked.connect(self.save)
        self.PB_cancel.clicked.connect(self.close)
        self.connection = connection

        authors = [(i[0], i[1]) for i in self.connection.cursor().execute('select * from autoren')]
        for item in authors:
            self.CB_author.addItem(item[1], item[0])
        books = [(i[0], i[1]) for i in self.connection.cursor().execute('select * from bucher')]
        for item in books:
            self.CB_book.addItem(item[1], item[0])

    def save(self):
        if self.LE_name.text():
            temp = [self.LE_name.text(), str(self.CB_author.currentData()),
                    str(self.CB_book.currentData())]

            self.connection.cursor().execute('INSERT INTO Arbeit(Name, ID_Autor, ID_Bucher)'
                                             ' VALUES(?,?,?)', (temp[0], temp[1], temp[2]))

            ex.default_query()
            self.close()
        else:
            self.LE_name.setText('Введите произведение!!!')


class EditAuthor(QMainWindow):
    def __init__(self, information, connection):
        super().__init__()
        uic.loadUi('Dialog_Author.ui', self)
        self.PB_ready.clicked.connect(self.save)
        self.PB_cancel.clicked.connect(self.close)

        self.information = information
        information = information.split()
        self.LE_surname.setText(information[0])
        self.LE_name.setText(information[1])
        if len(information) == 3:
            self.LE_patronymic.setText(information[2])

        self.connection = connection

    def save(self):
        temp = [self.LE_surname.text(), self.LE_name.text(), self.LE_patronymic.text()]
        if temp[0] or temp[1]:
            if temp[2]:
                author = f'{temp[0]} {temp[1][0]}.{temp[2][0]}.'
            else:
                author = temp[0] + ' ' + temp[1]

            self.connection.cursor().execute('UPDATE Autoren SET Autor = ? WHERE Autor = ?',
                                             (author, self.information))

            ex.default_query()
            self.close()
        else:
            self.LE_surname.setText('Введите фамилию!!!')
            self.LE_name.setText('Введите имя!!!')


class EditBook(QMainWindow):
    def __init__(self, information, connection):
        super().__init__()
        uic.loadUi('Dialog_Book.ui', self)
        self.PB_ready.clicked.connect(self.save)
        self.PB_cancel.clicked.connect(self.close)
        self.connection = connection
        self.information = information[-1]

        self.LE_name.setText(information[0])
        self.LE_location.setText(information[1])
        self.LE_ph.setText(information[2])
        self.LE_pages.setText(str(information[3]))
        self.LE_year.setText(str(information[4]))
        self.LE_ISBN.setText(information[-1])

    def save(self):
        if self.LE_ISBN.text():
            temp = [self.LE_name.text(), self.LE_ISBN.text(), self.LE_ph.text(),
                    self.LE_pages.text(),
                    self.LE_year.text(), self.LE_location.text()]

            self.connection.cursor().execute("""update Bucher 
    set Name_des_Buches = ?, ISBN = ?, verlag = ?, seitenzahl = ?, Erscheinungsjahr = ?, lage = ? 
    where ISBN = ?""", (temp[0], temp[1], temp[2], temp[3], temp[4], temp[5], temp[1],))

            ex.default_query()
            self.close()
        else:
            self.LE_ISBN.setText('Введите ISBN!!!')


class EditWork(QMainWindow):
    def __init__(self, information, connection):
        super().__init__()
        uic.loadUi('Dialog_Work.ui', self)
        self.PB_ready.clicked.connect(self.save)
        self.PB_cancel.clicked.connect(self.close)
        self.connection = connection
        self.information = information

        self.LE_name.setText(information)

        authors = [(i[0], i[1]) for i in self.connection.cursor().execute('select * from autoren')]
        for item in authors:
            self.CB_author.addItem(item[1], item[0])
        books = [(i[0], i[1]) for i in self.connection.cursor().execute('select * from bucher')]
        for item in books:
            self.CB_book.addItem(item[1], item[0])

    def save(self):
        if self.LE_name.text():
            temp = [self.LE_name.text(), str(self.CB_author.currentData()),
                    str(self.CB_book.currentData())]

            self.connection.cursor().execute("update Arbeit set Name = ?, "
                                             "ID_Autor = ?, ID_Bucher = ? where Name = ?",
                                             (temp[0], temp[1], temp[2], self.information))

            ex.default_query()
            self.close()
        else:
            self.LE_name.setText('Введите произведение!!!')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    ex = Main()
    ex.show()
    sys.exit(app.exec())
