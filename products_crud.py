import sqlite3
import sys

from openpyxl import Workbook
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)


DB_NAME = "products.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS Products (
                productID INTEGER PRIMARY KEY AUTOINCREMENT,
                productName TEXT NOT NULL,
                productPrice INTEGER NOT NULL
            )
            """
        )


def add_product(product_name, product_price):
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO Products (productName, productPrice) VALUES (?, ?)",
            (product_name, product_price),
        )
        return cursor.lastrowid


def update_product(product_id, product_name, product_price):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE Products
            SET productName = ?, productPrice = ?
            WHERE productID = ?
            """,
            (product_name, product_price, product_id),
        )
        return cursor.rowcount


def delete_product(product_id):
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM Products WHERE productID = ?",
            (product_id,),
        )
        return cursor.rowcount


def get_product_by_id(product_id):
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT productID, productName, productPrice FROM Products WHERE productID = ?",
            (product_id,),
        )
        return cursor.fetchone()


def search_products(keyword):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT productID, productName, productPrice
            FROM Products
            WHERE productName LIKE ?
            ORDER BY productID
            """,
            (f"%{keyword}%",),
        )
        return cursor.fetchall()


def list_products():
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT productID, productName, productPrice FROM Products ORDER BY productID"
        )
        return cursor.fetchall()


class ProductWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Products CRUD")
        self.setFixedSize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setStyleSheet(
            """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #1e293b);
            }
            QLabel {
                color: #e2e8f0;
                font-size: 14px;
                font-weight: 600;
            }
            QLabel#titleLabel {
                color: #f8fafc;
                font-size: 28px;
                font-weight: 900;
                letter-spacing: 2px;
                padding: 12px 0;
            }
            QLineEdit {
                background: rgba(255, 255, 255, 0.92);
                border: 2px solid #38bdf8;
                border-radius: 10px;
                padding: 8px 12px;
                color: #0f172a;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #f59e0b;
                background: #ffffff;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
            QPushButton#deleteButton {
                background-color: #ef4444;
            }
            QPushButton#deleteButton:hover {
                background-color: #dc2626;
            }
            QPushButton#exportButton {
                background-color: #10b981;
            }
            QPushButton#exportButton:hover {
                background-color: #059669;
            }
            QTableWidget {
                background: rgba(15, 23, 42, 0.92);
                alternate-background-color: rgba(30, 41, 59, 0.92);
                color: #e2e8f0;
                gridline-color: #334155;
                border: 1px solid #475569;
                border-radius: 12px;
                selection-background-color: #0ea5e9;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #38bdf8;
                color: #0f172a;
                padding: 8px;
                border: none;
                font-weight: 800;
            }
            """
        )

        main_layout = QVBoxLayout(central_widget)

        title = QLabel("Products 관리")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        form_layout = QGridLayout()
        main_layout.addLayout(form_layout)

        self.product_id_input = QLineEdit()
        self.product_id_input.setPlaceholderText("예: 1")
        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText("상품명을 입력하세요")
        self.product_price_input = QLineEdit()
        self.product_price_input.setPlaceholderText("숫자만 입력")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색할 이름을 입력하세요")

        form_layout.addWidget(QLabel("Product ID"), 0, 0)
        form_layout.addWidget(self.product_id_input, 0, 1)
        form_layout.addWidget(QLabel("Product Name"), 1, 0)
        form_layout.addWidget(self.product_name_input, 1, 1)
        form_layout.addWidget(QLabel("Product Price"), 2, 0)
        form_layout.addWidget(self.product_price_input, 2, 1)
        form_layout.addWidget(QLabel("Search Keyword"), 3, 0)
        form_layout.addWidget(self.search_input, 3, 1)

        button_row_1 = QHBoxLayout()
        button_row_2 = QHBoxLayout()
        main_layout.addLayout(button_row_1)
        main_layout.addLayout(button_row_2)

        self.add_button = QPushButton("입력")
        self.update_button = QPushButton("수정")
        self.delete_button = QPushButton("삭제")
        self.delete_button.setObjectName("deleteButton")
        self.search_id_button = QPushButton("ID 검색")
        self.search_name_button = QPushButton("이름 검색")
        self.list_button = QPushButton("전체 조회")
        self.export_button = QPushButton("엑셀 저장")
        self.export_button.setObjectName("exportButton")

        button_row_1.addWidget(self.add_button)
        button_row_1.addWidget(self.update_button)
        button_row_1.addWidget(self.delete_button)

        button_row_2.addWidget(self.search_id_button)
        button_row_2.addWidget(self.search_name_button)
        button_row_2.addWidget(self.list_button)
        button_row_2.addWidget(self.export_button)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Product ID", "Product Name", "Product Price"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        main_layout.addWidget(self.table)

        self.add_button.clicked.connect(self.add_product_data)
        self.update_button.clicked.connect(self.update_product_data)
        self.delete_button.clicked.connect(self.delete_product_data)
        self.search_id_button.clicked.connect(self.search_product_by_id)
        self.search_name_button.clicked.connect(self.search_products_by_name)
        self.list_button.clicked.connect(self.load_all_products)
        self.export_button.clicked.connect(self.export_to_excel)
        self.table.itemDoubleClicked.connect(self.fill_form_from_table)

        initialize_db()
        self.load_all_products()

    def show_message(self, title, message):
        QMessageBox.information(self, title, message)

    def show_error(self, title, message):
        QMessageBox.warning(self, title, message)

    def get_int_value(self, line_edit, field_name):
        text = line_edit.text().strip()
        if not text:
            raise ValueError(f"{field_name}을(를) 입력하세요.")
        return int(text)

    def collect_row_data(self):
        product_name = self.product_name_input.text().strip()
        if not product_name:
            raise ValueError("Product Name을 입력하세요.")

        product_price = self.get_int_value(self.product_price_input, "Product Price")
        return product_name, product_price

    def set_table_rows(self, rows):
        self.table.setRowCount(0)
        for row_data in rows:
            row_number = self.table.rowCount()
            self.table.insertRow(row_number)
            for column, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_number, column, item)

    def load_all_products(self):
        self.set_table_rows(list_products())

    def fill_form_from_table(self, item):
        row = item.row()
        product_id_item = self.table.item(row, 0)
        product_name_item = self.table.item(row, 1)
        product_price_item = self.table.item(row, 2)

        if product_id_item is None or product_name_item is None or product_price_item is None:
            return

        self.product_id_input.setText(product_id_item.text())
        self.product_name_input.setText(product_name_item.text())
        self.product_price_input.setText(product_price_item.text())
        self.search_input.clear()
        self.table.selectRow(row)

    def add_product_data(self):
        try:
            product_name, product_price = self.collect_row_data()
            new_id = add_product(product_name, product_price)
            self.show_message("완료", f"입력되었습니다. 새 Product ID: {new_id}")
            self.load_all_products()
        except ValueError as error:
            self.show_error("입력 오류", str(error))

    def update_product_data(self):
        try:
            product_id = self.get_int_value(self.product_id_input, "Product ID")
            product_name, product_price = self.collect_row_data()
            updated_rows = update_product(product_id, product_name, product_price)
            if updated_rows == 0:
                self.show_error("수정 실패", "해당 ID의 데이터를 찾을 수 없습니다.")
                return
            self.show_message("완료", "수정되었습니다.")
            self.load_all_products()
        except ValueError as error:
            self.show_error("입력 오류", str(error))

    def delete_product_data(self):
        try:
            product_id = self.get_int_value(self.product_id_input, "Product ID")
            deleted_rows = delete_product(product_id)
            if deleted_rows == 0:
                self.show_error("삭제 실패", "해당 ID의 데이터를 찾을 수 없습니다.")
                return
            self.show_message("완료", "삭제되었습니다.")
            self.load_all_products()
        except ValueError as error:
            self.show_error("입력 오류", str(error))

    def search_product_by_id(self):
        try:
            product_id = self.get_int_value(self.product_id_input, "Product ID")
            product = get_product_by_id(product_id)
            if product is None:
                self.show_error("검색 결과", "해당 ID의 데이터를 찾을 수 없습니다.")
                self.set_table_rows([])
                return
            self.set_table_rows([product])
        except ValueError as error:
            self.show_error("입력 오류", str(error))

    def search_products_by_name(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            self.show_error("입력 오류", "Search Keyword를 입력하세요.")
            return
        rows = search_products(keyword)
        self.set_table_rows(rows)

    def export_to_excel(self):
        rows = []
        for row in range(self.table.rowCount()):
            row_values = []
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                row_values.append(item.text() if item else "")
            rows.append(row_values)

        if not rows:
            self.show_error("저장 실패", "저장할 데이터가 없습니다.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "엑셀 파일 저장",
            "products.xlsx",
            "Excel Files (*.xlsx)",
        )

        if not file_path:
            return

        if not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Products"
        worksheet.append(["Product ID", "Product Name", "Product Price"])

        for row_values in rows:
            worksheet.append(row_values)

        workbook.save(file_path)
        self.show_message("완료", f"엑셀 파일로 저장했습니다.\n{file_path}")


def main():
    initialize_db()
    app = QApplication(sys.argv)
    window = ProductWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()