"""
每日计划制定程序 - PySide6 版入口
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from main_window import MainWindow, GLOBAL_STYLE


def main():
    # 高分屏适配（必须在创建 QApplication 之前）
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
