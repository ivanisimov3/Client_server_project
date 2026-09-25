# Точка входа

import sys
import psycopg2
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from database import (
    delete_main_rows,
    filters_are_empty,
    insert_main_row,
    load_lookup_values,
    search_main_rows,
    update_main_rows,
)
from window import MainWindow, UpdateDialog


def main():
    app = QApplication(sys.argv)

    try:
        lookup_values = load_lookup_values()
        main_rows, _ = search_main_rows({})
    except psycopg2.Error:
        QMessageBox.critical(
            None,
            "Ошибка базы данных",
            "Не удалось подключиться к PostgreSQL или загрузить данные. "
            "Проверьте, что сервер запущен, параметры в файле .env указаны верно "
            "и необходимые таблицы существуют.",
        )
        return 1

    window = MainWindow(lookup_values)
    window.show_rows(main_rows)

    def handle_search():
        try:
            rows, executed_query = search_main_rows(window.current_filters())
        except psycopg2.Error as exc:
            QMessageBox.critical(
                window,
                "Ошибка поиска",
                f"Не удалось выполнить поиск:\n{exc}",
            )
            return
        window.show_rows(rows)
        QMessageBox.information(window, "SQL-запрос", executed_query)

    window.buttons["search"].clicked.connect(handle_search) # Привязываем операцию к кнопке
    window.buttons["search"].setEnabled(True)

    def handle_add():
        try:
            added_row, executed_query = insert_main_row(window.current_insert_values())
        except ValueError as exc:
            QMessageBox.warning(window, "Ошибка добавления", str(exc)) # Исправляемая ошибка — warning
            return
        except psycopg2.Error as exc:
            QMessageBox.critical(window, "Ошибка добавления", str(exc)) # Ошибка работы с БД — critical
            return
        window.show_rows([added_row])
        window.clear_fields()
        QMessageBox.information(window, "SQL-запрос", executed_query)

    window.buttons["add"].clicked.connect(handle_add)
    window.buttons["add"].setEnabled(True)

    def handle_delete():
        filters = window.current_filters()
        try:
            rows, _ = search_main_rows(filters)
            if not rows:
                QMessageBox.information(window, "Удаление", "Записи по заданным условиям не найдены")
                return

            if filters_are_empty(filters) and not window.confirm_delete_all_rows():
                return
            if not window.confirm_delete(len(rows)):
                return

            executed_query = delete_main_rows(filters)
        except psycopg2.Error as exc:
            QMessageBox.critical(window, "Ошибка удаления", str(exc))
            return

        window.show_deleted_rows(rows)
        window.clear_fields()
        QMessageBox.information(window, "SQL-запрос", executed_query)

    window.buttons["delete"].clicked.connect(handle_delete)
    window.buttons["delete"].setEnabled(True)

    def handle_update():
        filters = window.current_filters()
        dialog = UpdateDialog(lookup_values, window)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            changes = dialog.current_changes()
            rows, _ = search_main_rows(filters)
            if not rows:
                QMessageBox.information(window, "Изменение", "Записи по заданным условиям не найдены")
                return

            if filters_are_empty(filters) and not window.confirm_update_all_rows():
                return
            if not window.confirm_update(len(rows)):
                return

            updated_rows, executed_query = update_main_rows(filters, changes)
        except psycopg2.Error as exc:
            QMessageBox.critical(window, "Ошибка изменения", str(exc))
            return

        window.show_rows(updated_rows)
        window.clear_fields()
        QMessageBox.information(window, "SQL-запрос", executed_query)

    window.buttons["update"].clicked.connect(handle_update)
    window.buttons["update"].setEnabled(True)

    window.buttons["reset"].clicked.connect(window.clear_fields)
    window.buttons["reset"].setEnabled(True)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
