# Главное окно приложения

from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


LOOKUP_FIELDS = (
    ("Фамилия", "fam_id"),
    ("Имя", "nam_id"),
    ("Отчество", "otc_id"),
    ("Улица", "strt_id"),
)

TEXT_FIELDS = (
    ("Дом", "bldn", 8),
    ("Корпус", "bldn_k", 8),
    ("Квартира", "apprt", 12),
    ("Телефон", "phone", 30),
)


class MainWindow(QMainWindow):

    def __init__(self, lookup_values):
        super().__init__()

        self.setWindowTitle("Клиентская часть")

        # Двухколонночная форма, состоящая из названия слева и виджета справа
        form = QFormLayout()
        self.lookup_boxes = {}
        for label, key in LOOKUP_FIELDS:
            box = QComboBox() # Выпадающий список
            box.addItem("Не выбрано", None) # Добавление элемента в выпадающий список с видимым значением и userData
            for item_id, value in lookup_values[key]:
                box.addItem(value if value is not None else "(пустое значение)", item_id)
            box.setCurrentIndex(0) # Элемент по умолчанию у выпадающего списка
            form.addRow(label, box) # Добавляем элементы вида <Название - Виджет> в форму
            self.lookup_boxes[key] = box # Сохраняем выпадающие списки, чтобы удобно обращаться

        # ---

        self.text_fields = {}
        for label, key, max_length in TEXT_FIELDS:
            field = QLineEdit() # Форма свободного ввода
            field.setMaxLength(max_length)
            form.addRow(label, field)
            self.text_fields[key] = field

        # ---

        button_row = QHBoxLayout() # Горизонтальный контейнер
        self.buttons = {}
        buttons = (
            ("Поиск", "search"),
            ("Добавить", "add"),
            ("Удалить", "delete"),
            ("Изменить", "update"),
            ("Сбросить", "reset"),
        )
        for label, key in buttons:
            button = QPushButton(label) # Кнопка
            button.setEnabled(False)
            button_row.addWidget(button)
            self.buttons[key] = button

        # ---

        self.result_table = QTableWidget(0, 9) # Таблица
        self.result_table.setHorizontalHeaderLabels((
            "UID", "Фамилия", "Имя", "Отчество", "Улица",
            "Дом", "Корпус", "Квартира", "Телефон",
        ))
        self.result_table.verticalHeader().setVisible(False) # Убираем автоматическую нумерацию строк
        self.result_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers # Запрещаем редактирование
        )
        self.result_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows # Выделение всей строки, если клик по элементу
        )

        # ---

        layout = QVBoxLayout() # Вертикальный контейнер
        layout.addLayout(form)
        layout.addLayout(button_row)
        layout.addWidget(self.result_table, 1)

        container = QWidget()
        container.setLayout(layout) # Располагаем элементы внутри QWidget
        self.setCentralWidget(container) # Распологаем контейнер на область central widget
        self.resize(940, 650)

    # Показать строки
    def show_rows(self, rows):
        self.result_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                text = "" if value is None else str(value)
                self.result_table.setItem(row_index, column_index, QTableWidgetItem(text)) # Кладем элемент в ячейку таблицы

    # Возвращаем пары <id, box> для каждого выпадающего списка
    def selected_lookup_ids(self):
        return {
            key: box.currentData() for key, box in self.lookup_boxes.items()
        }

    # Возвращаем пары <id, box> как для выпадающих списков, так и для тектовых форм
    def current_filters(self):
        filters = self.selected_lookup_ids()
        filters.update({key: field.text() for key, field in self.text_fields.items()})
        return filters

    # Подготовить значения для новой записи, пустой текст делаем None
    def current_insert_values(self):
        values = self.current_filters()
        for key in self.text_fields:
            if values[key] == "":
                values[key] = None
        return values

    # Очистить поля и списки
    def clear_fields(self):
        for box in self.lookup_boxes.values():
            box.setCurrentIndex(0)
        for field in self.text_fields.values():
            field.clear()

    # Подтверждение удаления найденных строк
    def confirm_delete(self, count):
        answer = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Найдено записей для удаления: {count}.\nУдалить их?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No, # По умолчанию отказ
        )
        return answer == QMessageBox.StandardButton.Yes

    # Предупреждение, когда ни одно поле фильтра не заполнено
    def confirm_delete_all_rows(self):
        answer = QMessageBox.warning(
            self,
            "Удаление всех записей",
            "Фильтры не заполнены. Удаление затронет все записи таблицы main.\nПродолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    # Подтверждение изменения найденных строк
    def confirm_update(self, count):
        answer = QMessageBox.question(
            self,
            "Подтверждение изменения",
            f"Найдено записей для изменения: {count}.\nИзменить их?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    # Отдельное предупреждение перед изменением всей таблицы main
    def confirm_update_all_rows(self):
        answer = QMessageBox.warning(
            self,
            "Изменение всех записей",
            "Фильтры не заполнены. Изменение затронет все записи таблицы main.\nПродолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    # Показывать красный список удалённых строк после успешного DELETE
    def show_deleted_rows(self, rows):
        self.show_rows(rows)
        red_text = QBrush(QColor("#a30000"))
        pale_red = QBrush(QColor("#ffe6e6"))
        for row_index in range(len(rows)):
            for column_index in range(self.result_table.columnCount()):
                item = self.result_table.item(row_index, column_index)
                item.setForeground(red_text)
                item.setBackground(pale_red)


class UpdateDialog(QDialog):

    def __init__(self, lookup_values, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Изменить на")

        form = QFormLayout()
        self.lookup_boxes = {}
        for label, key in LOOKUP_FIELDS:
            box = QComboBox()
            box.addItem("Не изменять", None)
            for item_id, value in lookup_values[key]:
                box.addItem(value if value is not None else "(пустое значение)", item_id)
            form.addRow(label, box)
            self.lookup_boxes[key] = box

        # ---

        self.text_fields = {}
        for label, key, max_length in TEXT_FIELDS:
            field = QLineEdit()
            field.setMaxLength(max_length)
            field.setPlaceholderText("Не изменять") # Подсказка, пока пользователь ничего не ввел
            form.addRow(label, field)
            self.text_fields[key] = field

        # ---

        continue_button = QPushButton("Продолжить")
        continue_button.clicked.connect(self.accept_changes)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)

        button_row = QHBoxLayout()
        button_row.addWidget(continue_button)
        button_row.addWidget(cancel_button)

        # ---

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(button_row)
        self.setLayout(layout)
        self.resize(360, 340)

    def accept_changes(self):
        if not self.current_changes():
            QMessageBox.warning(self, "Ошибка изменения", "Выберите хотя бы одно поле для изменения")
            return
        self.accept()

    # Только выбранные новые значения попадут в будущий SET
    def current_changes(self):
        changes = {
            key: box.currentData() 
            for key, box in self.lookup_boxes.items()
            if box.currentIndex() > 0
        }
        changes.update({
            key: field.text()
            for key, field in self.text_fields.items()
            if field.text() != ""
        })
        return changes
